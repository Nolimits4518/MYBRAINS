import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import OTPInput from 'react-otp-input';
import { 
  Plus, 
  Trash2, 
  Eye, 
  EyeOff, 
  Shield, 
  Link, 
  Unlink, 
  AlertTriangle,
  CheckCircle,
  Settings,
  Globe,
  Zap,
  Key,
  Smartphone,
  Mail,
  QrCode,
  Copy,
  Download
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// 🔐 2FA Setup Modal
const TwoFASetupModal = ({ isOpen, onClose, onSave, platformId }) => {
  const [setupStep, setSetupStep] = useState('method');
  const [twoFAMethod, setTwoFAMethod] = useState('totp');
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && setupStep === 'setup') {
      generateQRCode();
    }
  }, [isOpen, setupStep]);

  const generateQRCode = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/2fa/generate-setup`, null, {
        params: { account_name: `Platform ${platformId}`, issuer: 'Neural RSI System' }
      });
      
      if (response.data.status === 'success') {
        setQrCode(response.data.data.qr_code);
        setSecret(response.data.data.secret);
        setBackupCodes(response.data.data.backup_codes);
      }
    } catch (error) {
      console.error('Failed to generate 2FA setup:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyAndSave = async () => {
    try {
      setLoading(true);
      
      // Verify the code first
      const verifyResponse = await axios.post(`${BACKEND_URL}/api/2fa/verify`, {
        platform_id: platformId,
        code: verificationCode
      });

      if (verifyResponse.data.valid) {
        onSave({
          method: twoFAMethod,
          secret,
          backupCodes
        });
        onClose();
        setSetupStep('method');
        setVerificationCode('');
      } else {
        alert('Invalid verification code. Please try again.');
      }
    } catch (error) {
      console.error('2FA verification failed:', error);
      alert('Failed to verify 2FA code');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="holo-card p-8 max-w-md w-full mx-4"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="section-title text-xl">🔐 2FA Security Setup</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>

        {setupStep === 'method' && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-mono text-cyan-400 mb-3">Select 2FA Method</label>
              <div className="space-y-3">
                <label className="flex items-center space-x-3 p-3 border border-gray-600 rounded-lg hover:border-cyan-400 cursor-pointer">
                  <input
                    type="radio"
                    value="totp"
                    checked={twoFAMethod === 'totp'}
                    onChange={(e) => setTwoFAMethod(e.target.value)}
                    className="text-cyan-400"
                  />
                  <Smartphone className="w-5 h-5 text-cyan-400" />
                  <div>
                    <div className="font-medium">Authenticator App</div>
                    <div className="text-sm text-gray-400">Google Authenticator, Authy, etc.</div>
                  </div>
                </label>

                <label className="flex items-center space-x-3 p-3 border border-gray-600 rounded-lg hover:border-cyan-400 cursor-pointer">
                  <input
                    type="radio"
                    value="sms"
                    checked={twoFAMethod === 'sms'}
                    onChange={(e) => setTwoFAMethod(e.target.value)}
                    className="text-cyan-400"
                  />
                  <Mail className="w-5 h-5 text-cyan-400" />
                  <div>
                    <div className="font-medium">SMS</div>
                    <div className="text-sm text-gray-400">Text message to phone</div>
                  </div>
                </label>
              </div>
            </div>

            <div className="flex space-x-3">
              <button onClick={onClose} className="flex-1 px-4 py-2 border border-gray-600 rounded-lg hover:border-gray-400">
                Cancel
              </button>
              <button 
                onClick={() => setSetupStep('setup')} 
                className="flex-1 neon-button"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {setupStep === 'setup' && twoFAMethod === 'totp' && (
          <div className="space-y-6">
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-4">Scan this QR code with your authenticator app:</p>
              {qrCode ? (
                <img src={qrCode} alt="QR Code" className="mx-auto mb-4 border border-cyan-400/30 rounded-lg" />
              ) : (
                <div className="w-48 h-48 mx-auto bg-gray-800 rounded-lg flex items-center justify-center">
                  {loading ? 'Generating...' : <QrCode className="w-12 h-12 text-gray-600" />}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-mono text-cyan-400 mb-2">Manual Entry Secret:</label>
              <div className="flex items-center space-x-2 p-3 bg-gray-800/50 rounded-lg border border-gray-600">
                <code className="flex-1 text-xs font-mono text-green-400">{secret}</code>
                <button 
                  onClick={() => navigator.clipboard.writeText(secret)}
                  className="p-1 hover:bg-gray-700 rounded"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-mono text-cyan-400 mb-2">Enter Verification Code:</label>
              <OTPInput
                value={verificationCode}
                onChange={setVerificationCode}
                numInputs={6}
                separator={<span className="mx-1">-</span>}
                inputStyle={{
                  width: '3rem',
                  height: '3rem',
                  margin: '0 0.25rem',
                  fontSize: '1.2rem',
                  borderRadius: '0.5rem',
                  border: '1px solid #4B5563',
                  backgroundColor: '#374151',
                  color: '#ffffff',
                  textAlign: 'center'
                }}
                focusStyle={{
                  border: '1px solid #00F5FF',
                  outline: 'none'
                }}
              />
            </div>

            <div className="flex space-x-3">
              <button onClick={() => setSetupStep('method')} className="flex-1 px-4 py-2 border border-gray-600 rounded-lg hover:border-gray-400">
                Back
              </button>
              <button 
                onClick={verifyAndSave}
                disabled={verificationCode.length !== 6 || loading}
                className="flex-1 neon-button neon-button-success disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify & Save'}
              </button>
            </div>
          </div>
        )}

        {backupCodes.length > 0 && (
          <motion.div 
            className="mt-6 p-4 bg-yellow-900/20 border border-yellow-600/30 rounded-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <h4 className="font-semibold text-yellow-400 mb-2">⚠️ Backup Codes</h4>
            <p className="text-xs text-gray-400 mb-3">Save these backup codes safely. You can use them if you lose access to your authenticator:</p>
            <div className="grid grid-cols-2 gap-2">
              {backupCodes.map((code, index) => (
                <code key={index} className="text-xs p-2 bg-gray-800 rounded font-mono">
                  {code}
                </code>
              ))}
            </div>
          </motion.div>
        )}
      </motion.div>
    </motion.div>
  );
};

// 🌐 Platform Connection Card
const PlatformCard = ({ platform, onConnect, onDisconnect, onDelete, onTrade, onViewInterface, onClosePosition }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleConnect = async () => {
    setLoading(true);
    await onConnect(platform.platform_id);
    setLoading(false);
  };

  const handleDisconnect = async () => {
    setLoading(true);
    await onDisconnect(platform.platform_id);
    setLoading(false);
  };

  return (
    <motion.div 
      className="holo-card p-6"
      whileHover={{ y: -2 }}
      layout
    >
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-bold text-lg text-white">{platform.platform_name}</h3>
          <p className="text-sm text-gray-400 font-mono">{platform.username}</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            platform.is_connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
          }`} />
          <span className={`text-xs font-mono ${
            platform.is_connected ? 'text-green-400' : 'text-red-400'
          }`}>
            {platform.is_connected ? 'CONNECTED' : 'OFFLINE'}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center text-sm text-gray-400">
          <Globe className="w-4 h-4 mr-2" />
          <span className="truncate">{platform.login_url}</span>
        </div>
        
        <div className="flex items-center text-sm text-gray-400">
          <Shield className="w-4 h-4 mr-2" />
          <span>{platform.two_fa_enabled ? '2FA Enabled' : 'Basic Auth'}</span>
        </div>

        <div className="flex items-center text-sm text-gray-400">
          <Key className="w-4 h-4 mr-2" />
          <span>Added {new Date(platform.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mt-6">
        {platform.is_connected ? (
          <>
            <button
              onClick={() => onTrade(platform)}
              className="neon-button neon-button-success text-sm"
            >
              <Zap className="w-4 h-4 mr-1" />
              Trade
            </button>
            <button
              onClick={() => onViewInterface(platform)}
              className="neon-button text-sm"
            >
              <Eye className="w-4 h-4 mr-1" />
              Interface
            </button>
            <button
              onClick={() => onClosePosition(platform)}
              className="neon-button text-sm"
            >
              <Target className="w-4 h-4 mr-1" />
              Close Position
            </button>
            <button
              onClick={handleDisconnect}
              disabled={loading}
              className="px-3 py-2 border border-yellow-600 text-yellow-400 rounded-lg hover:bg-yellow-600/10 disabled:opacity-50 text-sm"
            >
              <Unlink className="w-4 h-4" />
            </button>
          </>
        ) : (
          <>
            <button
              onClick={handleConnect}
              disabled={loading}
              className="neon-button text-sm"
            >
              {loading ? (
                <div className="cyber-loader w-4 h-4 mr-1" />
              ) : (
                <Link className="w-4 h-4 mr-1" />
              )}
              Connect
            </button>
            <button
              onClick={() => onDelete(platform.platform_id)}
              className="px-3 py-2 border border-red-600 text-red-400 rounded-lg hover:bg-red-600/10 text-sm"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </motion.div>
  );
};

// 📝 Add Platform Modal
const AddPlatformModal = ({ isOpen, onClose, onAdd }) => {
  const [step, setStep] = useState(1);
  const [platformName, setPlatformName] = useState('');
  const [loginUrl, setLoginUrl] = useState('');
  const [detectedForm, setDetectedForm] = useState(null);
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    server: '',
    additionalFields: {}
  });
  const [enable2FA, setEnable2FA] = useState(false);
  const [twoFAConfig, setTwoFAConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [show2FASetup, setShow2FASetup] = useState(false);

  const analyzePlatform = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/platform/analyze`, {
        platform_name: platformName,
        login_url: loginUrl
      });
      
      if (response.data.status === 'success') {
        setDetectedForm(response.data.data);
        setStep(2);
      }
    } catch (error) {
      console.error('Platform analysis failed:', error);
      alert('Failed to analyze platform. Please check the URL and try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderFormField = (field) => {
    const fieldValue = credentials[field.name] || credentials.additionalFields[field.name] || '';
    
    const updateFieldValue = (value) => {
      if (['username', 'password', 'server'].includes(field.name)) {
        setCredentials({...credentials, [field.name]: value});
      } else {
        setCredentials({
          ...credentials,
          additionalFields: {
            ...credentials.additionalFields,
            [field.name]: value
          }
        });
      }
    };

    const fieldClasses = "w-full px-4 py-3 bg-gray-800/50 border border-cyan-400/30 rounded-lg text-white font-mono focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30";
    
    switch (field.type) {
      case 'password':
        return (
          <div key={field.name} className="relative">
            <input
              type={showPassword ? "text" : "password"}
              value={fieldValue}
              onChange={(e) => updateFieldValue(e.target.value)}
              placeholder={field.placeholder}
              className={`${fieldClasses} pr-12`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-cyan-400"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>
        );
      
      case 'select':
        return (
          <select
            key={field.name}
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            className={fieldClasses}
          >
            <option value="">{field.placeholder}</option>
            {field.options?.map((option, index) => (
              <option key={index} value={option}>{option}</option>
            )) || [
              <option key="demo" value="demo">Demo Server</option>,
              <option key="live" value="live">Live Server</option>,
              <option key="staging" value="staging">Staging Server</option>
            ]}
          </select>
        );
      
      case 'email':
        return (
          <input
            key={field.name}
            type="email"
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            placeholder={field.placeholder}
            className={fieldClasses}
          />
        );
      
      case 'tel':
        return (
          <input
            key={field.name}
            type="tel"
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            placeholder={field.placeholder}
            className={fieldClasses}
          />
        );
      
      case 'number':
        return (
          <input
            key={field.name}
            type="number"
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            placeholder={field.placeholder}
            className={fieldClasses}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            key={field.name}
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            placeholder={field.placeholder}
            className={`${fieldClasses} h-24 resize-none`}
          />
        );
      
      default: // text
        return (
          <input
            key={field.name}
            type="text"
            value={fieldValue}
            onChange={(e) => updateFieldValue(e.target.value)}
            placeholder={field.placeholder}
            className={fieldClasses}
          />
        );
    }
  };

  const savePlatform = async () => {
    try {
      setLoading(true);
      
      const response = await axios.post(`${BACKEND_URL}/api/platform/save-credentials`, {
        platform_id: `${platformName.toLowerCase()}_${Date.now()}`,
        username: credentials.username,
        password: credentials.password,
        server: credentials.server,
        additional_fields: credentials.additionalFields,
        enable_2fa: enable2FA,
        two_fa_method: twoFAConfig?.method || 'none',
        totp_secret: twoFAConfig?.secret || '',
        backup_codes: twoFAConfig?.backupCodes || []
      });

      if (response.data.status === 'success') {
        onAdd();
        onClose();
        resetForm();
      }
    } catch (error) {
      console.error('Failed to save platform:', error);
      alert('Failed to save platform credentials');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setStep(1);
    setPlatformName('');
    setLoginUrl('');
    setDetectedForm(null);
    setCredentials({ username: '', password: '', server: '', additionalFields: {} });
    setEnable2FA(false);
    setTwoFAConfig(null);
  };

  if (!isOpen) return null;

  return (
    <motion.div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="holo-card p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="section-title text-2xl flex items-center">
            <Plus className="w-6 h-6 mr-2" />
            Add Trading Platform
          </h3>
          <button onClick={() => { onClose(); resetForm(); }} className="text-gray-400 hover:text-white">✕</button>
        </div>

        {/* Step 1: Platform URL */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-mono text-cyan-400 mb-3">Platform Name</label>
              <input
                type="text"
                value={platformName}
                onChange={(e) => setPlatformName(e.target.value)}
                placeholder="e.g., Binance, Coinbase, Custom Platform"
                className="w-full px-4 py-3 bg-gray-800/50 border border-cyan-400/30 rounded-lg text-white font-mono focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30"
              />
            </div>

            <div>
              <label className="block text-sm font-mono text-cyan-400 mb-3">Login URL</label>
              <input
                type="url"
                value={loginUrl}
                onChange={(e) => setLoginUrl(e.target.value)}
                placeholder="https://platform.com/login"
                className="w-full px-4 py-3 bg-gray-800/50 border border-cyan-400/30 rounded-lg text-white font-mono focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30"
              />
              <p className="text-xs text-gray-400 mt-2">
                🔍 We'll analyze this page to detect login form fields automatically
              </p>
            </div>

            <div className="flex space-x-3">
              <button 
                onClick={() => { onClose(); resetForm(); }} 
                className="flex-1 px-6 py-3 border border-gray-600 rounded-lg hover:border-gray-400"
              >
                Cancel
              </button>
              <button 
                onClick={analyzePlatform}
                disabled={!platformName || !loginUrl || loading}
                className="flex-1 neon-button disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="cyber-loader w-4 h-4 mr-2" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4 mr-2" />
                    Analyze Platform
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Detected Form & Credentials */}
        {step === 2 && detectedForm && (
          <div className="space-y-6">
            <div className="bg-green-900/20 border border-green-600/30 rounded-lg p-4">
              <h4 className="font-semibold text-green-400 mb-2">✅ Platform Analysis Complete</h4>
              <div className="text-sm text-gray-300 space-y-1">
                <p>• Found {detectedForm.login_fields.length} login fields</p>
                <p>• 2FA Support: {detectedForm.two_fa_detected ? '✅ Detected' : '❌ Not detected'}</p>
                <p>• CAPTCHA: {detectedForm.captcha_detected ? '⚠️ Detected' : '✅ None'}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {detectedForm.login_fields.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">
                    {field.label}
                    {field.required && <span className="text-red-400 ml-1">*</span>}
                  </label>
                  {renderFormField(field)}
                </div>
              ))}
            </div>

            <div className="border-t border-gray-700 pt-6">
              <div className="flex items-center justify-between mb-4">
                <label className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    checked={enable2FA}
                    onChange={(e) => setEnable2FA(e.target.checked)}
                    className="w-5 h-5 text-cyan-400 bg-gray-800 border-cyan-400/30 rounded focus:ring-cyan-400/30"
                  />
                  <span className="text-sm font-mono text-cyan-400">Enable 2FA Security</span>
                </label>
                
                {enable2FA && (
                  <button
                    onClick={() => setShow2FASetup(true)}
                    className="text-sm neon-button px-4 py-1"
                  >
                    Setup 2FA
                  </button>
                )}
              </div>

              {twoFAConfig && (
                <div className="bg-green-900/20 border border-green-600/30 rounded-lg p-3">
                  <p className="text-sm text-green-400">
                    ✅ 2FA configured with {twoFAConfig.method.toUpperCase()}
                  </p>
                </div>
              )}
            </div>

            <div className="flex space-x-3">
              <button onClick={() => setStep(1)} className="flex-1 px-6 py-3 border border-gray-600 rounded-lg hover:border-gray-400">
                Back
              </button>
              <button 
                onClick={savePlatform}
                disabled={!credentials.username || !credentials.password || loading}
                className="flex-1 neon-button neon-button-success disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <div className="cyber-loader w-4 h-4 mr-2" />
                    Saving...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Save Platform
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        <TwoFASetupModal
          isOpen={show2FASetup}
          onClose={() => setShow2FASetup(false)}
          onSave={(config) => setTwoFAConfig(config)}
          platformId="new_platform"
        />
      </motion.div>
    </motion.div>
  );
};

// 🚀 Main Platform Connector Component
const PlatformConnector = () => {
  const [platforms, setPlatforms] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showInterfaceModal, setShowInterfaceModal] = useState(false);
  const [showClosePositionModal, setShowClosePositionModal] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [interfaceData, setInterfaceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlatforms();
  }, []);

  const fetchPlatforms = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/platform/list`);
      if (response.data.status === 'success') {
        setPlatforms(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch platforms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platformId) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/platform/connect/${platformId}`);
      if (response.data.status === 'success') {
        fetchPlatforms(); // Refresh list
      } else {
        alert('Connection failed: ' + response.data.message);
      }
    } catch (error) {
      console.error('Connection failed:', error);
      alert('Failed to connect to platform');
    }
  };

  const handleDisconnect = async (platformId) => {
    try {
      await axios.post(`${BACKEND_URL}/api/platform/disconnect/${platformId}`);
      fetchPlatforms(); // Refresh list
    } catch (error) {
      console.error('Disconnection failed:', error);
    }
  };

  const handleDelete = async (platformId) => {
    if (window.confirm('Are you sure you want to delete this platform? This action cannot be undone.')) {
      try {
        await axios.delete(`${BACKEND_URL}/api/platform/${platformId}`);
        fetchPlatforms(); // Refresh list
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const handleTrade = (platform) => {
    // This would open a trade modal - for now just show an alert
    alert(`Trading on ${platform.platform_name} - Feature coming soon!`);
  };

  const handleViewInterface = async (platform) => {
    try {
      setSelectedPlatform(platform);
      setShowInterfaceModal(true);
      
      const response = await axios.get(`${BACKEND_URL}/api/platform/interface/${platform.platform_id}`);
      if (response.data.status === 'success') {
        setInterfaceData(response.data.data);
      }
    } catch (error) {
      console.error('Failed to fetch interface data:', error);
      alert('Failed to load interface analysis');
    }
  };

  const handleClosePosition = (platform) => {
    setSelectedPlatform(platform);
    setShowClosePositionModal(true);
  };

  const handleClosePositionSubmit = async (positionSymbol) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/platform/close-position`, {
        platform_id: selectedPlatform.platform_id,
        position_symbol: positionSymbol
      });
      
      if (response.data.status === 'success') {
        alert(`Position ${positionSymbol} closed successfully!`);
        setShowClosePositionModal(false);
      } else {
        alert('Failed to close position: ' + response.data.message);
      }
    } catch (error) {
      console.error('Close position failed:', error);
      alert('Failed to close position');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="section-title text-2xl flex items-center">
          <Globe className="w-6 h-6 mr-3" />
          Universal Platform Connector
        </h2>
        <button
          onClick={() => setShowAddModal(true)}
          className="neon-button flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Platform
        </button>
      </div>

      <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-4">
        <h3 className="font-semibold text-blue-400 mb-2">🔗 Universal Trading Integration</h3>
        <p className="text-sm text-gray-300">
          Connect to ANY trading platform by providing login credentials. Our system will automatically 
          detect form fields, handle 2FA authentication, analyze trading interface, and execute trades on your behalf.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="cyber-loader w-12 h-12 mx-auto mb-4" />
          <p className="text-gray-400">Scanning connected platforms...</p>
        </div>
      ) : platforms.length === 0 ? (
        <div className="text-center py-12">
          <Globe className="w-16 h-16 mx-auto text-gray-600 mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">No Platforms Connected</h3>
          <p className="text-gray-500 mb-6">
            Add your first trading platform to start universal trading
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="neon-button neon-button-success"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Your First Platform
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {platforms.map((platform) => (
            <PlatformCard
              key={platform.platform_id}
              platform={platform}
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              onDelete={handleDelete}
              onTrade={handleTrade}
              onViewInterface={handleViewInterface}
              onClosePosition={handleClosePosition}
            />
          ))}
        </div>
      )}

      <AddPlatformModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={fetchPlatforms}
      />

      <InterfaceAnalysisModal
        isOpen={showInterfaceModal}
        onClose={() => setShowInterfaceModal(false)}
        platform={selectedPlatform}
        interfaceData={interfaceData}
      />

      <ClosePositionModal
        isOpen={showClosePositionModal}
        onClose={() => setShowClosePositionModal(false)}
        platform={selectedPlatform}
        onSubmit={handleClosePositionSubmit}
      />
    </div>
  );
};

export default PlatformConnector;