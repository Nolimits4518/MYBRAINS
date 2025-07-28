import React, { useState, useEffect } from 'react';
import './App.css';
import AutomationInterface from './AutomationInterface';

function App() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState('');
  const [botStatus, setBotStatus] = useState(null);
  const [scanStatus, setScanStatus] = useState(null);
  const [scanSettings, setScanSettings] = useState({
    interval_minutes: 15,
    mode: 'normal'
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchSignals();
    checkBotStatus();
    fetchScanStatus();
    
    const statusInterval = setInterval(() => {
      if (scanStatus?.active) {
        fetchScanStatus();
      }
    }, 10000);

    return () => clearInterval(statusInterval);
  }, [scanStatus?.active]);

  const fetchSignals = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/signals`);
      const data = await response.json();
      setSignals(data.signals);
    } catch (error) {
      console.error('Error fetching signals:', error);
    }
  };

  const checkBotStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/test-telegram`);
      const data = await response.json();
      setBotStatus(data);
    } catch (error) {
      console.error('Telegram bot connection failed:', error);
      setBotStatus({ status: 'error', message: error.message });
    }
  };

  const fetchScanStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/scan-status`);
      const data = await response.json();
      setScanStatus(data);
    } catch (error) {
      console.error('Error fetching scan status:', error);
    }
  };

  const updateScanSettings = async (newSettings) => {
    try {
      const response = await fetch(`${backendUrl}/api/update-scan-settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newSettings,
          chat_id: parseInt(chatId) || null
        })
      });

      if (response.ok) {
        const data = await response.json();
        setScanSettings(newSettings);
        fetchScanStatus();
        alert(data.message);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert(`Network error: ${error.message}`);
    }
  };

  const sendTestSignal = async () => {
    if (!chatId) {
      alert('Please enter your Telegram Chat ID');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/send-test-signal?chat_id=${chatId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Test signal sent successfully! Signal ID: ${data.signal_id}`);
        fetchSignals();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      alert(`Network error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startMonitoring = async () => {
    if (!chatId) {
      alert('Please enter your Telegram Chat ID first');
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/start-monitoring`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchScanStatus();
        alert(`Monitoring started! Scanning every ${scanSettings.interval_minutes} minutes.`);
      }
    } catch (error) {
      alert(`Error starting monitoring: ${error.message}`);
    }
  };

  const stopMonitoring = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/stop-monitoring`, {
        method: 'POST'
      });
      if (response.ok) {
        fetchScanStatus();
        alert('Monitoring stopped!');
      }
    } catch (error) {
      alert(`Error stopping monitoring: ${error.message}`);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatNextScan = (nextScan) => {
    if (!nextScan) return 'N/A';
    const next = new Date(nextScan);
    const now = new Date();
    const diff = Math.max(0, Math.floor((next - now) / 1000 / 60));
    return diff > 0 ? `${diff}m` : 'Now';
  };

  const getChainColor = (chain) => {
    const colors = {
      'Solana': 'bg-purple-100 text-purple-800',
      'Ethereum': 'bg-blue-100 text-blue-800',
      'Polygon': 'bg-indigo-100 text-indigo-800',
      'BSC': 'bg-yellow-100 text-yellow-800'
    };
    return colors[chain] || 'bg-gray-100 text-gray-800';
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getModeColor = (mode) => {
    const colors = {
      'aggressive': 'bg-red-100 text-red-800',
      'normal': 'bg-blue-100 text-blue-800',
      'conservative': 'bg-green-100 text-green-800'
    };
    return colors[mode] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-800/50 to-blue-800/50"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              🚀 Memecoin Signal Bot
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Real-time monitoring with SMART CONTRACT AUTOMATION for your Phantom wallet
            </p>
            
            {/* Status Panel */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {/* Bot Status */}
              <div className="flex justify-center">
                {botStatus?.status === 'connected' ? (
                  <div className="inline-flex items-center px-4 py-2 bg-green-500/20 border border-green-400 rounded-lg">
                    <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
                    <span className="text-green-300">Bot Connected: @{botStatus.bot_username}</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center px-4 py-2 bg-red-500/20 border border-red-400 rounded-lg">
                    <div className="w-2 h-2 bg-red-400 rounded-full mr-2"></div>
                    <span className="text-red-300">Bot Connection Failed</span>
                  </div>
                )}
              </div>

              {/* Scan Status */}
              <div className="flex justify-center">
                {scanStatus?.active ? (
                  <div className="inline-flex items-center px-4 py-2 bg-blue-500/20 border border-blue-400 rounded-lg">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></div>
                    <span className="text-blue-300">
                      Scanning: {formatNextScan(scanStatus.next_scan)} until next
                    </span>
                  </div>
                ) : (
                  <div className="inline-flex items-center px-4 py-2 bg-gray-500/20 border border-gray-400 rounded-lg">
                    <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
                    <span className="text-gray-300">Monitoring Inactive</span>
                  </div>
                )}
              </div>
            </div>

            {/* Control Panel */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 max-w-6xl mx-auto border border-white/20">
              <h3 className="text-xl font-semibold text-white mb-6">🎛️ Control Panel</h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Column 1: Basic Controls */}
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-white">📱 Basic Setup</h4>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Telegram Chat ID
                    </label>
                    <input
                      type="text"
                      value={chatId}
                      onChange={(e) => setChatId(e.target.value)}
                      placeholder="Enter your Telegram Chat ID"
                      className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Get your Chat ID by messaging @userinfobot on Telegram
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    <button
                      onClick={sendTestSignal}
                      disabled={loading || !chatId}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                    >
                      {loading ? 'Sending...' : '📢 Test Signal'}
                    </button>

                    <button
                      onClick={scanStatus?.active ? stopMonitoring : startMonitoring}
                      disabled={!chatId && !scanStatus?.active}
                      className={`px-4 py-2 text-white rounded-lg font-medium transition-all duration-200 ${
                        scanStatus?.active 
                          ? 'bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-700 hover:to-orange-700' 
                          : 'bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {scanStatus?.active ? '⏹️ Stop Monitor' : '🔍 Start Monitor'}
                    </button>
                  </div>
                </div>

                {/* Column 2: Scan Settings */}
                <div className="space-y-4">
                  <h4 className="text-lg font-medium text-white">⚙️ Scan Settings</h4>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Scan Interval: {scanSettings.interval_minutes} minutes
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="120"
                      step="1"
                      value={scanSettings.interval_minutes}
                      onChange={(e) => setScanSettings({...scanSettings, interval_minutes: parseInt(e.target.value)})}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>1m</span>
                      <span>30m</span>
                      <span>60m</span>
                      <span>120m</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Scan Mode
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {['aggressive', 'normal', 'conservative'].map((mode) => (
                        <button
                          key={mode}
                          onClick={() => setScanSettings({...scanSettings, mode})}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                            scanSettings.mode === mode
                              ? 'bg-purple-600 text-white'
                              : 'bg-white/10 text-gray-300 hover:bg-white/20'
                          }`}
                        >
                          {mode.charAt(0).toUpperCase() + mode.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => updateScanSettings(scanSettings)}
                    className="w-full px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 font-medium transition-all duration-200"
                  >
                    💾 Update Scan Settings
                  </button>
                </div>

                {/* Column 3: Smart Contract Automation */}
                <AutomationInterface chatId={chatId} backendUrl={backendUrl} />
              </div>

              {/* Status Info */}
              {scanStatus && (
                <div className="mt-6 p-4 bg-black/20 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-sm text-gray-400">Mode</div>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${getModeColor(scanStatus.mode)}`}>
                        {scanStatus.mode?.toUpperCase()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Interval</div>
                      <div className="text-white font-medium">{scanStatus.interval_minutes}m</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Scans Today</div>
                      <div className="text-white font-medium">{scanStatus.scans_today}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Signals Today</div>
                      <div className="text-white font-medium">{scanStatus.signals_today}/5</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="text-3xl mb-4">🛡️</div>
            <h3 className="text-xl font-semibold text-white mb-2">Rug-Pull Protection</h3>
            <p className="text-gray-300">Advanced filtering to detect revoked authorities, locked liquidity, and safe holder distribution.</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="text-3xl mb-4">📈</div>
            <h3 className="text-xl font-semibold text-white mb-2">Profit Potential</h3>
            <p className="text-gray-300">AI-powered analysis of market cap, volume trends, and social sentiment for maximum gains.</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="text-3xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold text-white mb-2">Real-Time Alerts</h3>
            <p className="text-gray-300">Instant Telegram notifications for pre-launch opportunities across Solana, Ethereum, and more.</p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <div className="text-3xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-white mb-2">Smart Contract Automation</h3>
            <p className="text-gray-300">Safe automated trading with spending limits, safety thresholds, and emergency controls.</p>
          </div>
        </div>

        {/* Recent Signals */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20 overflow-hidden">
          <div className="px-6 py-4 border-b border-white/20">
            <h2 className="text-2xl font-bold text-white">Recent Signals</h2>
            <p className="text-gray-300">Latest memecoin opportunities detected by our monitoring system</p>
          </div>
          
          <div className="divide-y divide-white/10">
            {signals.length > 0 ? (
              signals.map((signal, index) => (
                <div key={signal.id || index} className="px-6 py-4 hover:bg-white/5 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-semibold text-white">
                        {signal.name} (${signal.symbol})
                      </h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getChainColor(signal.chain)}`}>
                        {signal.chain}
                      </span>
                      {signal.type === 'auto_signal' && (
                        <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          AUTO
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-400">
                      {formatTimestamp(signal.timestamp)}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-400">Market Cap</p>
                      <p className="text-white font-medium">${signal.market_cap?.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Liquidity</p>
                      <p className="text-white font-medium">${signal.liquidity?.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Safety Score</p>
                      <p className={`font-bold ${getScoreColor(signal.safety_score)}`}>
                        {signal.safety_score}/10
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Profit Potential</p>
                      <p className={`font-bold ${getScoreColor(signal.profit_potential)}`}>
                        {signal.profit_potential}/10
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400">Social Score</p>
                      <p className={`font-bold ${getScoreColor(signal.social_score)}`}>
                        {signal.social_score}/10
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <code className="text-xs bg-black/30 px-2 py-1 rounded text-gray-300 flex-1 mr-3">
                      {signal.contract_address}
                    </code>
                    <div className="flex space-x-2">
                      {signal.chain === 'Solana' && (
                        <a 
                          href={`https://jup.ag/swap/SOL-${signal.contract_address}`}
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-purple-400 hover:text-purple-300 transition-colors px-2 py-1 bg-purple-900/30 rounded"
                        >
                          🟣 Jupiter
                        </a>
                      )}
                      <a 
                        href={`https://dexscreener.com/${signal.chain.toLowerCase()}/${signal.contract_address}`}
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-green-400 hover:text-green-300 transition-colors px-2 py-1 bg-green-900/30 rounded"
                      >
                        📊 Chart
                      </a>
                      <button 
                        onClick={() => navigator.clipboard.writeText(signal.contract_address)}
                        className="text-sm text-gray-400 hover:text-gray-300 transition-colors px-2 py-1 bg-gray-900/30 rounded"
                        title="Copy contract address"
                      >
                        📋 Copy
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-12 text-center">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-lg font-medium text-white mb-2">No signals yet</h3>
                <p className="text-gray-400">Send a test signal or start monitoring to see results here</p>
              </div>
            )}
          </div>
        </div>

        {/* Smart Contract Automation Explanation */}
        <div className="mt-12 bg-gradient-to-r from-green-500/10 to-blue-500/10 backdrop-blur-lg rounded-xl p-6 border border-green-400/20">
          <div className="flex items-center mb-4">
            <span className="text-3xl mr-3">🤖</span>
            <h2 className="text-2xl font-bold text-white">Smart Contract Automation Features</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">🛡️ Maximum Safety</h3>
              <ul className="text-gray-300 space-y-1 text-sm">
                <li>• Spending limits prevent large losses</li>
                <li>• Safety score thresholds filter risky tokens</li>
                <li>• Emergency stop available anytime</li>
                <li>• No private key exposure or storage</li>
                <li>• Transparent on-chain operations</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">⚡ Lightning Fast</h3>
              <ul className="text-gray-300 space-y-1 text-sm">
                <li>• Execute trades in milliseconds</li>
                <li>• Beat manual traders to opportunities</li>
                <li>• 24/7 monitoring while you sleep</li>
                <li>• No more missed moon shots</li>
                <li>• Automatic slippage optimization</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">🎛️ Full Control</h3>
              <ul className="text-gray-300 space-y-1 text-sm">
                <li>• Adjust limits anytime</li>
                <li>• Revoke permissions instantly</li>
                <li>• Monitor all activity via Telegram</li>
                <li>• Your wallet, your rules</li>
                <li>• Detailed transaction logging</li>
              </ul>
            </div>
          </div>
          <div className="mt-4 p-4 bg-yellow-500/10 rounded-lg border border-yellow-400/20">
            <p className="text-yellow-200 text-sm">
              <strong>⚠️ Important:</strong> Smart contract automation uses Phantom's built-in approval system. 
              You maintain full control and can revoke permissions instantly. Start with small amounts to test the system.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/20 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-400">
            <p className="mb-2">⚠️ <strong>Disclaimer:</strong> High-risk investment. Smart contract automation is experimental. DYOR and only invest what you can afford to lose.</p>
            <p className="text-sm">Built with FastAPI + React + MongoDB + Solana Smart Contracts | Max 5 signals per day</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;