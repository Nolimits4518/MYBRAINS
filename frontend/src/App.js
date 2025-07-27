import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatId, setChatId] = useState('');
  const [botStatus, setBotStatus] = useState(null);
  const [monitoringActive, setMonitoringActive] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    fetchSignals();
    checkBotStatus();
  }, []);

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
    try {
      const response = await fetch(`${backendUrl}/api/start-monitoring`, {
        method: 'POST'
      });
      if (response.ok) {
        setMonitoringActive(true);
        alert('Memecoin monitoring started!');
      }
    } catch (error) {
      alert(`Error starting monitoring: ${error.message}`);
    }
  };

  const sendWeeklyReport = async () => {
    if (!chatId) {
      alert('Please enter your Telegram Chat ID');
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/send-weekly-report?chat_id=${chatId}`, {
        method: 'POST'
      });
      if (response.ok) {
        alert('Weekly report sent to Telegram!');
      }
    } catch (error) {
      alert(`Error sending report: ${error.message}`);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
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
              Real-time monitoring and Telegram alerts for high-potential, low-risk memecoin opportunities
            </p>
            
            {/* Bot Status */}
            <div className="mb-8">
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

            {/* Control Panel */}
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 max-w-2xl mx-auto border border-white/20">
              <h3 className="text-xl font-semibold text-white mb-4">Control Panel</h3>
              
              <div className="space-y-4">
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

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={sendTestSignal}
                    disabled={loading || !chatId}
                    className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                  >
                    {loading ? 'Sending...' : '📢 Send Test Signal'}
                  </button>

                  <button
                    onClick={startMonitoring}
                    disabled={monitoringActive}
                    className="px-4 py-2 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                  >
                    {monitoringActive ? '🟢 Monitoring Active' : '🔍 Start Monitoring'}
                  </button>

                  <button
                    onClick={sendWeeklyReport}
                    disabled={!chatId}
                    className="px-4 py-2 bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-lg hover:from-orange-700 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
                  >
                    📊 Weekly Report
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
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
                    <code className="text-xs bg-black/30 px-2 py-1 rounded text-gray-300">
                      {signal.contract_address}
                    </code>
                    <button className="text-sm text-purple-400 hover:text-purple-300 transition-colors">
                      Add to Phantom →
                    </button>
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

        {/* Telegram Commands */}
        <div className="mt-12 bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
          <h3 className="text-xl font-semibold text-white mb-4">Telegram Bot Commands</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-black/20 rounded-lg p-4">
              <code className="text-purple-400">/check [contract_address]</code>
              <p className="text-sm text-gray-300 mt-2">Get real-time token safety analysis</p>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <code className="text-purple-400">/stats</code>
              <p className="text-sm text-gray-300 mt-2">View signal performance statistics</p>
            </div>
            <div className="bg-black/20 rounded-lg p-4">
              <code className="text-purple-400">/help</code>
              <p className="text-sm text-gray-300 mt-2">Show all available commands</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/20 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-400">
            <p className="mb-2">⚠️ <strong>Disclaimer:</strong> High-risk investment. DYOR and only invest what you can afford to lose.</p>
            <p className="text-sm">Built with FastAPI + React + MongoDB | Max 5 signals per day</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;