import asyncio
import json
import logging
import os
import base64
import pyotp
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
from urllib.parse import urlparse, urljoin
import aiohttp
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from selenium_stealth import stealth
from cryptography.fernet import Fernet
import hashlib
import secrets

# 🔐 Security and Encryption
class SecurityManager:
    def __init__(self):
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        key_file = "encryption.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

# 📝 Data Models
class Platform(Enum):
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKEX = "okex"
    HUOBI = "huobi"
    KUCOIN = "kucoin"
    BITFINEX = "bitfinex"
    CUSTOM = "custom"

class AuthMethod(Enum):
    NONE = "none"
    SMS = "sms"
    TOTP = "totp"
    EMAIL = "email"
    YUBIKEY = "yubikey"
    PUSH = "push"

class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    CANCEL = "cancel"

@dataclass
class LoginField:
    name: str
    selector: str
    type: str  # text, password, email, etc.
    label: str
    required: bool = True
    placeholder: str = ""

@dataclass
class TwoFAConfig:
    enabled: bool = False
    method: AuthMethod = AuthMethod.NONE
    backup_codes: List[str] = None
    totp_secret: str = ""
    sms_number: str = ""
    email: str = ""

@dataclass
class PlatformCredentials:
    platform_id: str
    platform_name: str
    login_url: str
    username: str
    password: str
    api_key: str = ""
    api_secret: str = ""
    two_fa: TwoFAConfig = None
    created_at: str = ""
    last_used: str = ""
    is_active: bool = True

@dataclass
class DetectedForm:
    login_fields: List[LoginField]
    submit_button: str
    two_fa_detected: bool = False
    captcha_detected: bool = False
    additional_fields: List[LoginField] = None

@dataclass
class TradeOrder:
    symbol: str
    action: TradeAction
    quantity: float
    price: Optional[float] = None
    order_type: str = "market"  # market, limit, stop
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: str = "GTC"

@dataclass
class TradeResult:
    success: bool
    order_id: str
    message: str
    filled_quantity: float = 0
    filled_price: float = 0
    timestamp: str = ""

# 🕷️ Web Automation Engine
class WebAutomator:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    async def start_browser(self, headless: bool = True):
        """Start browser with stealth configuration"""
        try:
            self.playwright = await async_playwright().start()
            
            # Browser configuration for maximum stealth
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--window-size=1920,1080'
                ]
            )
            
            # Create stealth context
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                java_script_enabled=True,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            
            self.page = await self.context.new_page()
            
            # Inject stealth scripts
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)
            
            logging.info("🚀 Browser started with stealth configuration")
            
        except Exception as e:
            logging.error(f"❌ Failed to start browser: {e}")
            raise
    
    async def analyze_login_page(self, url: str) -> DetectedForm:
        """Analyze login page and detect form fields"""
        try:
            await self.page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # Detect form fields
            login_fields = []
            
            # Enhanced selectors for comprehensive form detection
            field_selectors = {
                'username': [
                    'input[name*="user"]', 'input[name*="email"]', 'input[name*="login"]',
                    'input[id*="user"]', 'input[id*="email"]', 'input[id*="login"]',
                    'input[type="email"]', 'input[placeholder*="user"]', 'input[placeholder*="email"]',
                    'input[placeholder*="Username"]', 'input[placeholder*="Email"]'
                ],
                'password': [
                    'input[type="password"]', 'input[name*="pass"]', 'input[id*="pass"]',
                    'input[placeholder*="password"]', 'input[placeholder*="Password"]'
                ],
                'server': [
                    'select[name*="server"]', 'select[id*="server"]', 'select[name*="environment"]',
                    'select[id*="environment"]', 'input[name*="server"]', 'input[id*="server"]',
                    'select[placeholder*="server"]', 'select[placeholder*="Server"]',
                    'select[name*="broker"]', 'select[id*="broker"]'
                ],
                'additional_text': [
                    'input[name*="phone"]', 'input[name*="code"]', 'input[name*="pin"]',
                    'input[type="tel"]', 'input[type="number"]', 'input[name*="account"]',
                    'input[id*="account"]', 'input[name*="client"]', 'input[id*="client"]',
                    'input[name*="trading"]', 'input[id*="trading"]'
                ],
                'additional_select': [
                    'select[name*="country"]', 'select[id*="country"]', 'select[name*="region"]',
                    'select[id*="region"]', 'select[name*="platform"]', 'select[id*="platform"]'
                ]
            }
            
            # Detect all form elements in order
            all_inputs = await self.page.query_selector_all('input, select, textarea')
            
            for element in all_inputs:
                if not await element.is_visible():
                    continue
                    
                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                input_type = await element.get_attribute('type') or 'text'
                name = await element.get_attribute('name') or ''
                element_id = await element.get_attribute('id') or ''
                placeholder = await element.get_attribute('placeholder') or ''
                
                # Skip hidden and submit inputs
                if input_type in ['hidden', 'submit', 'button', 'reset']:
                    continue
                
                # Determine field type and label
                field_type = 'text'
                label = 'Unknown Field'
                
                # Check for password fields
                if input_type == 'password':
                    field_type = 'password'
                    label = 'Password'
                
                # Check for email fields
                elif input_type == 'email' or any(keyword in (name + element_id + placeholder).lower() 
                                                for keyword in ['email', 'mail']):
                    field_type = 'email'
                    label = 'Email'
                
                # Check for username fields
                elif any(keyword in (name + element_id + placeholder).lower() 
                        for keyword in ['user', 'login', 'account']):
                    field_type = 'text'
                    label = 'Username'
                
                # Check for server/broker selection fields
                elif (tag_name == 'select' and 
                      any(keyword in (name + element_id + placeholder).lower() 
                          for keyword in ['server', 'broker', 'environment', 'platform'])):
                    field_type = 'select'
                    label = 'Server/Broker'
                    
                    # Try to get options for select fields
                    try:
                        options = await element.query_selector_all('option')
                        option_values = []
                        for option in options:
                            option_text = await option.text_content()
                            option_value = await option.get_attribute('value')
                            if option_text and option_text.strip():
                                option_values.append(option_text.strip())
                        if option_values:
                            placeholder = f"Options: {', '.join(option_values[:3])}" + ('...' if len(option_values) > 3 else '')
                    except:
                        pass
                
                # Check for phone fields
                elif input_type == 'tel' or any(keyword in (name + element_id + placeholder).lower() 
                                               for keyword in ['phone', 'mobile', 'tel']):
                    field_type = 'tel'
                    label = 'Phone'
                
                # Check for country/region fields
                elif (tag_name == 'select' and 
                      any(keyword in (name + element_id + placeholder).lower() 
                          for keyword in ['country', 'region', 'location'])):
                    field_type = 'select'
                    label = 'Country/Region'
                
                # Check for numeric fields
                elif input_type == 'number' or any(keyword in (name + element_id + placeholder).lower() 
                                                  for keyword in ['code', 'pin', 'number']):
                    field_type = 'number'
                    label = 'Code/Number'
                
                # Check for text areas
                elif tag_name == 'textarea':
                    field_type = 'textarea'
                    label = 'Text Area'
                
                # Default text field
                elif tag_name == 'input' and input_type == 'text':
                    field_type = 'text'
                    if placeholder:
                        label = placeholder.title()
                    else:
                        label = name.title() if name else 'Text Field'
                
                # Only add if we found a relevant field
                if field_type and label != 'Unknown Field':
                    field_name = name or element_id or field_type
                    
                    # Create appropriate selector
                    if name:
                        selector = f'{tag_name}[name="{name}"]'
                    elif element_id:
                        selector = f'{tag_name}[id="{element_id}"]'
                    else:
                        selector = f'{tag_name}[type="{input_type}"]' if input_type else tag_name
                    
                    login_fields.append(LoginField(
                        name=field_name,
                        selector=selector,
                        type=field_type,
                        label=label,
                        placeholder=placeholder or f'Enter {label.lower()}'
                    ))
            
            # Detect submit button
            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]', 
                'button:contains("login")', 'button:contains("sign in")',
                '.login-button', '#login-button', '.submit-button'
            ]
            
            submit_button = ""
            for selector in submit_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    submit_button = selector
                    break
            
            # Detect 2FA presence
            two_fa_indicators = [
                'input[name*="2fa"]', 'input[name*="totp"]', 'input[name*="code"]',
                '.two-factor', '.2fa', '.authentication'
            ]
            
            two_fa_detected = False
            for indicator in two_fa_indicators:
                if await self.page.query_selector(indicator):
                    two_fa_detected = True
                    break
            
            # Detect CAPTCHA
            captcha_indicators = [
                '.captcha', '.recaptcha', 'iframe[src*="recaptcha"]',
                'input[name*="captcha"]'
            ]
            
            captcha_detected = False
            for indicator in captcha_indicators:
                if await self.page.query_selector(indicator):
                    captcha_detected = True
                    break
            
            detected_form = DetectedForm(
                login_fields=login_fields,
                submit_button=submit_button,
                two_fa_detected=two_fa_detected,
                captcha_detected=captcha_detected
            )
            
            logging.info(f"✅ Detected {len(login_fields)} fields, 2FA: {two_fa_detected}, CAPTCHA: {captcha_detected}")
            return detected_form
            
        except Exception as e:
            logging.error(f"❌ Failed to analyze login page: {e}")
            raise
    
    async def perform_login(self, credentials: PlatformCredentials, detected_form: DetectedForm) -> bool:
        """Perform login with detected form"""
        try:
            await self.page.goto(credentials.login_url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Fill login form
            for field in detected_form.login_fields:
                if field.type == 'text' or 'user' in field.name.lower() or 'email' in field.name.lower():
                    await self.page.fill(field.selector, credentials.username)
                    logging.info(f"✅ Filled username field: {field.selector}")
                    
                elif field.type == 'password' or 'pass' in field.name.lower():
                    await self.page.fill(field.selector, credentials.password)
                    logging.info(f"✅ Filled password field: {field.selector}")
            
            await asyncio.sleep(1)
            
            # Click submit button
            if detected_form.submit_button:
                await self.page.click(detected_form.submit_button)
                logging.info(f"✅ Clicked submit button: {detected_form.submit_button}")
            else:
                # Try pressing Enter
                await self.page.press('body', 'Enter')
                logging.info("✅ Pressed Enter to submit")
            
            await asyncio.sleep(3)
            
            # Handle 2FA if detected
            if detected_form.two_fa_detected and credentials.two_fa and credentials.two_fa.enabled:
                await self._handle_2fa(credentials.two_fa)
            
            # Check if login was successful
            current_url = self.page.url
            if current_url != credentials.login_url and 'login' not in current_url.lower():
                logging.info("✅ Login successful - redirected away from login page")
                return True
            else:
                # Check for error messages
                error_selectors = ['.error', '.alert', '.warning', '[role="alert"]']
                for selector in error_selectors:
                    error_element = await self.page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        logging.error(f"❌ Login error detected: {error_text}")
                        return False
                
                logging.warning("⚠️ Login status unclear - may need manual verification")
                return False
            
        except Exception as e:
            logging.error(f"❌ Login failed: {e}")
            return False
    
    async def _handle_2fa(self, two_fa_config: TwoFAConfig) -> bool:
        """Handle 2FA authentication"""
        try:
            logging.info(f"🔐 Handling 2FA with method: {two_fa_config.method.value}")
            
            # Wait for 2FA input field
            two_fa_selectors = [
                'input[name*="2fa"]', 'input[name*="code"]', 'input[name*="token"]',
                'input[name*="authenticator"]', 'input[name*="verification"]'
            ]
            
            two_fa_field = None
            for selector in two_fa_selectors:
                field = await self.page.query_selector(selector)
                if field and await field.is_visible():
                    two_fa_field = selector
                    break
            
            if not two_fa_field:
                logging.error("❌ 2FA field not found")
                return False
            
            # Generate or get 2FA code
            code = ""
            if two_fa_config.method == AuthMethod.TOTP and two_fa_config.totp_secret:
                totp = pyotp.TOTP(two_fa_config.totp_secret)
                code = totp.now()
                logging.info(f"✅ Generated TOTP code: {code}")
            
            elif two_fa_config.method == AuthMethod.SMS:
                # For SMS, we'll need user input
                logging.info("📱 SMS 2FA detected - waiting for user input")
                # This will be handled by the frontend
                return True
            
            elif two_fa_config.method == AuthMethod.EMAIL:
                logging.info("📧 Email 2FA detected - waiting for user input")
                return True
            
            if code:
                await self.page.fill(two_fa_field, code)
                await asyncio.sleep(1)
                
                # Submit 2FA
                submit_button = await self.page.query_selector('button[type="submit"]')
                if submit_button:
                    await submit_button.click()
                else:
                    await self.page.press(two_fa_field, 'Enter')
                
                await asyncio.sleep(3)
                logging.info("✅ 2FA code submitted")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"❌ 2FA handling failed: {e}")
            return False
    
    async def execute_trade(self, order: TradeOrder, platform: str) -> TradeResult:
        """Execute trade on the connected platform"""
        try:
            logging.info(f"🔄 Executing {order.action.value} order for {order.symbol}")
            
            # Platform-specific trading logic
            if platform.lower() in ['binance', 'coinbase', 'kraken']:
                return await self._execute_standard_trade(order)
            else:
                return await self._execute_custom_platform_trade(order, platform)
                
        except Exception as e:
            logging.error(f"❌ Trade execution failed: {e}")
            return TradeResult(
                success=False,
                order_id="",
                message=f"Trade execution failed: {str(e)}"
            )
    
    async def _execute_standard_trade(self, order: TradeOrder) -> TradeResult:
        """Execute trade on standard platforms (Binance, Coinbase, etc.)"""
        try:
            # Navigate to trading page
            trading_selectors = {
                'symbol_input': ['input[placeholder*="symbol"]', '.symbol-input', '#symbol'],
                'quantity_input': ['input[placeholder*="quantity"]', '.quantity-input', '#quantity'],
                'price_input': ['input[placeholder*="price"]', '.price-input', '#price'],
                'buy_button': ['.buy-button', 'button:contains("buy")', '#buy-btn'],
                'sell_button': ['.sell-button', 'button:contains("sell")', '#sell-btn']
            }
            
            # Fill order details
            symbol_field = await self._find_element(trading_selectors['symbol_input'])
            if symbol_field:
                await self.page.fill(symbol_field, order.symbol)
            
            quantity_field = await self._find_element(trading_selectors['quantity_input'])
            if quantity_field:
                await self.page.fill(quantity_field, str(order.quantity))
            
            if order.price and order.order_type == 'limit':
                price_field = await self._find_element(trading_selectors['price_input'])
                if price_field:
                    await self.page.fill(price_field, str(order.price))
            
            # Click buy/sell button
            if order.action == TradeAction.BUY:
                buy_button = await self._find_element(trading_selectors['buy_button'])
                if buy_button:
                    await self.page.click(buy_button)
            elif order.action == TradeAction.SELL:
                sell_button = await self._find_element(trading_selectors['sell_button'])
                if sell_button:
                    await self.page.click(sell_button)
            
            await asyncio.sleep(2)
            
            # Confirm order if needed
            confirm_selectors = ['button:contains("confirm")', '.confirm-button', '#confirm']
            confirm_button = await self._find_element(confirm_selectors)
            if confirm_button:
                await self.page.click(confirm_button)
                await asyncio.sleep(2)
            
            # Check for success message or order ID
            order_id = await self._extract_order_id()
            
            return TradeResult(
                success=True,
                order_id=order_id,
                message="Trade executed successfully",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logging.error(f"❌ Standard trade execution failed: {e}")
            return TradeResult(
                success=False,
                order_id="",
                message=f"Trade execution failed: {str(e)}"
            )
    
    async def _find_element(self, selectors: List[str]) -> Optional[str]:
        """Find element using multiple selectors"""
        for selector in selectors:
            element = await self.page.query_selector(selector)
            if element and await element.is_visible():
                return selector
        return None
    
    async def _extract_order_id(self) -> str:
        """Extract order ID from success message or confirmation"""
        try:
            # Common patterns for order IDs
            order_id_selectors = [
                '.order-id', '#order-id', '[data-order-id]',
                '.transaction-id', '#transaction-id'
            ]
            
            for selector in order_id_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    order_id = await element.text_content()
                    if order_id and len(order_id) > 5:
                        return order_id.strip()
            
            # Try to extract from success message
            success_selectors = ['.success', '.confirmation', '.order-success']
            for selector in success_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    # Look for order ID patterns (alphanumeric, 8+ characters)
                    import re
                    matches = re.findall(r'[A-Za-z0-9]{8,}', text)
                    if matches:
                        return matches[0]
            
            return f"ORDER_{int(datetime.now().timestamp())}"
            
        except Exception as e:
            logging.error(f"❌ Failed to extract order ID: {e}")
            return f"ORDER_{int(datetime.now().timestamp())}"
    
    async def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logging.info("✅ Browser closed successfully")
            
        except Exception as e:
            logging.error(f"❌ Error closing browser: {e}")

# 🏢 Platform Connection Manager
class PlatformConnectionManager:
    def __init__(self):
        self.security = SecurityManager()
        self.automator = WebAutomator()
        self.credentials: Dict[str, PlatformCredentials] = {}
        self.active_connections: Dict[str, bool] = {}
        self.load_credentials()
    
    def save_credentials(self):
        """Save encrypted credentials to file"""
        try:
            credentials_data = {}
            for platform_id, creds in self.credentials.items():
                # Encrypt sensitive data
                encrypted_creds = {
                    "platform_id": creds.platform_id,
                    "platform_name": creds.platform_name,
                    "login_url": creds.login_url,
                    "username": self.security.encrypt(creds.username),
                    "password": self.security.encrypt(creds.password),
                    "api_key": self.security.encrypt(creds.api_key) if creds.api_key else "",
                    "api_secret": self.security.encrypt(creds.api_secret) if creds.api_secret else "",
                    "created_at": creds.created_at,
                    "last_used": creds.last_used,
                    "is_active": creds.is_active
                }
                
                if creds.two_fa:
                    encrypted_creds["two_fa"] = {
                        "enabled": creds.two_fa.enabled,
                        "method": creds.two_fa.method.value,
                        "totp_secret": self.security.encrypt(creds.two_fa.totp_secret) if creds.two_fa.totp_secret else "",
                        "sms_number": self.security.encrypt(creds.two_fa.sms_number) if creds.two_fa.sms_number else "",
                        "email": self.security.encrypt(creds.two_fa.email) if creds.two_fa.email else "",
                        "backup_codes": [self.security.encrypt(code) for code in (creds.two_fa.backup_codes or [])]
                    }
                
                credentials_data[platform_id] = encrypted_creds
            
            with open("platform_credentials.json", "w") as f:
                json.dump(credentials_data, f)
                
            logging.info("✅ Credentials saved successfully")
            
        except Exception as e:
            logging.error(f"❌ Failed to save credentials: {e}")
    
    def load_credentials(self):
        """Load and decrypt credentials from file"""
        try:
            if not os.path.exists("platform_credentials.json"):
                return
            
            with open("platform_credentials.json", "r") as f:
                credentials_data = json.load(f)
            
            for platform_id, encrypted_creds in credentials_data.items():
                # Decrypt sensitive data
                two_fa = None
                if "two_fa" in encrypted_creds and encrypted_creds["two_fa"]:
                    two_fa_data = encrypted_creds["two_fa"]
                    two_fa = TwoFAConfig(
                        enabled=two_fa_data["enabled"],
                        method=AuthMethod(two_fa_data["method"]),
                        totp_secret=self.security.decrypt(two_fa_data["totp_secret"]) if two_fa_data["totp_secret"] else "",
                        sms_number=self.security.decrypt(two_fa_data["sms_number"]) if two_fa_data["sms_number"] else "",
                        email=self.security.decrypt(two_fa_data["email"]) if two_fa_data["email"] else "",
                        backup_codes=[self.security.decrypt(code) for code in two_fa_data["backup_codes"]] if two_fa_data["backup_codes"] else []
                    )
                
                creds = PlatformCredentials(
                    platform_id=encrypted_creds["platform_id"],
                    platform_name=encrypted_creds["platform_name"],
                    login_url=encrypted_creds["login_url"],
                    username=self.security.decrypt(encrypted_creds["username"]),
                    password=self.security.decrypt(encrypted_creds["password"]),
                    api_key=self.security.decrypt(encrypted_creds["api_key"]) if encrypted_creds["api_key"] else "",
                    api_secret=self.security.decrypt(encrypted_creds["api_secret"]) if encrypted_creds["api_secret"] else "",
                    two_fa=two_fa,
                    created_at=encrypted_creds["created_at"],
                    last_used=encrypted_creds["last_used"],
                    is_active=encrypted_creds["is_active"]
                )
                
                self.credentials[platform_id] = creds
                self.active_connections[platform_id] = False
            
            logging.info(f"✅ Loaded {len(self.credentials)} platform credentials")
            
        except Exception as e:
            logging.error(f"❌ Failed to load credentials: {e}")
    
    async def add_platform(self, platform_name: str, login_url: str) -> DetectedForm:
        """Add new platform and analyze login form"""
        try:
            await self.automator.start_browser(headless=True)  # Use headless for production
            detected_form = await self.automator.analyze_login_page(login_url)
            await self.automator.close_browser()
            
            logging.info(f"✅ Platform {platform_name} analyzed successfully")
            return detected_form
            
        except Exception as e:
            logging.error(f"❌ Failed to add platform: {e}")
            # Clean up browser if it was started
            try:
                await self.automator.close_browser()
            except:
                pass
            
            # Return a fallback form structure
            logging.info(f"🔄 Using fallback form structure for {platform_name}")
            return DetectedForm(
                login_fields=[
                    LoginField(
                        name="username",
                        selector="input[name='username'], input[name='email'], input[type='email']",
                        type="text",
                        label="Username/Email",
                        placeholder="Enter your username or email"
                    ),
                    LoginField(
                        name="password",
                        selector="input[name='password'], input[type='password']",
                        type="password",
                        label="Password",
                        placeholder="Enter your password"
                    )
                ],
                submit_button="button[type='submit'], input[type='submit']",
                two_fa_detected=True,  # Assume 2FA is available
                captcha_detected=False
            )
    
    async def save_platform_credentials(self, platform_name: str, login_url: str, 
                                      username: str, password: str, 
                                      two_fa_config: Optional[TwoFAConfig] = None) -> str:
        """Save platform credentials"""
        try:
            platform_id = f"{platform_name.lower()}_{int(datetime.now().timestamp())}"
            
            credentials = PlatformCredentials(
                platform_id=platform_id,
                platform_name=platform_name,
                login_url=login_url,
                username=username,
                password=password,
                two_fa=two_fa_config,
                created_at=datetime.now().isoformat(),
                last_used="",
                is_active=True
            )
            
            self.credentials[platform_id] = credentials
            self.active_connections[platform_id] = False
            self.save_credentials()
            
            logging.info(f"✅ Platform credentials saved: {platform_id}")
            return platform_id
            
        except Exception as e:
            logging.error(f"❌ Failed to save platform credentials: {e}")
            raise
    
    async def connect_platform(self, platform_id: str) -> bool:
        """Connect to platform using saved credentials"""
        try:
            if platform_id not in self.credentials:
                raise ValueError(f"Platform {platform_id} not found")
            
            credentials = self.credentials[platform_id]
            
            await self.automator.start_browser(headless=True)
            detected_form = await self.automator.analyze_login_page(credentials.login_url)
            
            login_success = await self.automator.perform_login(credentials, detected_form)
            
            if login_success:
                self.active_connections[platform_id] = True
                credentials.last_used = datetime.now().isoformat()
                self.save_credentials()
                logging.info(f"✅ Connected to platform: {platform_id}")
                return True
            else:
                logging.error(f"❌ Failed to connect to platform: {platform_id}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Platform connection failed: {e}")
            return False
    
    async def execute_trade_on_platform(self, platform_id: str, order: TradeOrder) -> TradeResult:
        """Execute trade on connected platform"""
        try:
            if platform_id not in self.active_connections or not self.active_connections[platform_id]:
                # Try to connect first
                connected = await self.connect_platform(platform_id)
                if not connected:
                    return TradeResult(
                        success=False,
                        order_id="",
                        message="Platform not connected"
                    )
            
            credentials = self.credentials[platform_id]
            result = await self.automator.execute_trade(order, credentials.platform_name)
            
            logging.info(f"✅ Trade executed on {platform_id}: {result.order_id}")
            return result
            
        except Exception as e:
            logging.error(f"❌ Trade execution failed on {platform_id}: {e}")
            return TradeResult(
                success=False,
                order_id="",
                message=f"Trade execution failed: {str(e)}"
            )
    
    def get_connected_platforms(self) -> List[Dict]:
        """Get list of connected platforms"""
        platforms = []
        for platform_id, credentials in self.credentials.items():
            platforms.append({
                "platform_id": platform_id,
                "platform_name": credentials.platform_name,
                "login_url": credentials.login_url,
                "username": credentials.username,
                "is_connected": self.active_connections.get(platform_id, False),
                "last_used": credentials.last_used,
                "created_at": credentials.created_at,
                "two_fa_enabled": credentials.two_fa.enabled if credentials.two_fa else False
            })
        return platforms
    
    async def disconnect_platform(self, platform_id: str):
        """Disconnect from platform"""
        try:
            self.active_connections[platform_id] = False
            await self.automator.close_browser()
            logging.info(f"✅ Disconnected from platform: {platform_id}")
            
        except Exception as e:
            logging.error(f"❌ Failed to disconnect from platform: {e}")
    
    def delete_platform(self, platform_id: str) -> bool:
        """Delete platform credentials"""
        try:
            if platform_id in self.credentials:
                del self.credentials[platform_id]
                if platform_id in self.active_connections:
                    del self.active_connections[platform_id]
                self.save_credentials()
                logging.info(f"✅ Platform deleted: {platform_id}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"❌ Failed to delete platform: {e}")
            return False

# 🎯 2FA Helper Functions
class TwoFactorHelper:
    @staticmethod
    def generate_totp_qr(secret: str, account_name: str, issuer: str = "RSI Trading Bot") -> str:
        """Generate QR code for TOTP setup"""
        try:
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=account_name,
                issuer_name=issuer
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logging.error(f"❌ Failed to generate QR code: {e}")
            return ""
    
    @staticmethod
    def verify_totp_code(secret: str, code: str) -> bool:
        """Verify TOTP code"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=2)
        except Exception as e:
            logging.error(f"❌ TOTP verification failed: {e}")
            return False
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes"""
        return [secrets.token_hex(4).upper() for _ in range(count)]

# Global instance
platform_manager = PlatformConnectionManager()