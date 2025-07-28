import React, { useState, useEffect } from 'react';

const AutomationInterface = ({ chatId, backendUrl }) => {
  const [tradingStatus, setTradingStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoTradingConfig, setAutoTradingConfig] = useState({
    solana_wallet: '8PSCzs3itmfPrLzn3NbN1pPVGQhDimU1pZ2sz4k9tTiA',
    ethereum_wallet: '',
    base_wallet: '0x8C9658E97767A2c34a9bB8070674F092eEA36ff5',
    max_trade_amount_sol: 0.5,
    max_trade_amount_eth: 0.1,
    max_trade_amount_base: 0.1,
    max_daily_trades: 3,
    min_safety_score: 7.5,
    min_profit_score: 7.0,
    max_slippage_percent: 15,
    allowed_chains: ['Solana', 'Base']
  });

  useEffect(() => {
    fetchTradingStatus();
  }, []);

  const fetchTradingStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/trading-status`);
      const data = await response.json();
      setTradingStatus(data);
    } catch (error) {
      console.error('Error fetching trading status:', error);
      setTradingStatus({ error: 'Not configured' });
    }
  };

  const setupAutoTrading = async () => {
    if (!autoTradingConfig.solana_wallet && !autoTradingConfig.ethereum_wallet) {
      alert('Please enter at least one wallet address');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/setup-auto-trading`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(autoTradingConfig)
      });

      if (response.ok) {
        const data = await response.json();
        
        let walletInfo = 'Multi-chain automation setup:\n';
        Object.entries(data.wallets).forEach(([chain, wallet]) => {
          if (wallet !== "Not configured") {
            walletInfo += `${chain}: ${wallet}\n`;
          }
        });
        
        alert(`✅ ${data.message}!\n\n${walletInfo}\nBalance: ${data.wallet_balance}\n\nSafety Features:\n${data.safety_features.join('\n')}`);
        fetchTradingStatus();
      } else {
        const error = await response.json();
        alert(`❌ Setup Error: ${error.detail}`);
      }
    } catch (error) {
      alert(`❌ Network error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const emergencyStop = async () => {
    if (!confirm('🚨 EMERGENCY STOP 🚨\n\nThis will immediately halt ALL automated trading.\nAre you sure?')) {
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/emergency-stop`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('🛑 Emergency Stop Activated!\nAll automated trading has been stopped.');
        fetchTradingStatus();
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const revokePermissions = async () => {
    if (!confirm('⚠️ REVOKE ALL PERMISSIONS ⚠️\n\nThis will permanently disable automation and remove all trading permissions.\nYou will need to reconfigure everything.\nAre you sure?')) {
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/revoke-trading`, {
        method: 'POST'
      });

      if (response.ok) {
        alert('✅ All trading permissions have been revoked.\nAutomation is now completely disabled.');
        setTradingStatus(null);
        fetchTradingStatus();
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const getTradingStatusColor = (status) => {
    if (status === 'active') return 'bg-green-500/20 border-green-400 text-green-300';
    if (status === 'inactive') return 'bg-gray-500/20 border-gray-400 text-gray-300';
    return 'bg-red-500/20 border-red-400 text-red-300';
  };

  return (
    <div className="space-y-4">
      <h4 className="text-lg font-medium text-white">🤖 Smart Contract Automation</h4>
      
      {/* Trading Status Indicator */}
      <div className="flex justify-center mb-4">
        {tradingStatus && !tradingStatus.error ? (
          <div className={`inline-flex items-center px-4 py-2 border rounded-lg ${getTradingStatusColor(tradingStatus.status)}`}>
            <div className="w-2 h-2 rounded-full mr-2 animate-pulse bg-current"></div>
            <span>Auto-Trading: {tradingStatus.status?.toUpperCase()}</span>
          </div>
        ) : (
          <div className="inline-flex items-center px-4 py-2 bg-gray-500/20 border border-gray-400 rounded-lg">
            <div className="w-2 h-2 bg-gray-400 rounded-full mr-2"></div>
            <span className="text-gray-300">Auto-Trading: Not Setup</span>
          </div>
        )}
      </div>

      {!tradingStatus || tradingStatus.error ? (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              🟣 Solana Wallet Address
            </label>
            <input
              type="text"
              value={autoTradingConfig.solana_wallet}
              onChange={(e) => setAutoTradingConfig({...autoTradingConfig, solana_wallet: e.target.value})}
              placeholder="Enter your Solana wallet address"
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              🦄 Ethereum Wallet Address
            </label>
            <input
              type="text"
              value={autoTradingConfig.ethereum_wallet}
              onChange={(e) => setAutoTradingConfig({...autoTradingConfig, ethereum_wallet: e.target.value})}
              placeholder="Enter your Ethereum wallet address"
              className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-300 mb-1">Max Trade SOL</label>
              <input
                type="number"
                min="0.1"
                max="10"
                step="0.1"
                value={autoTradingConfig.max_trade_amount_sol}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, max_trade_amount_sol: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1">Max Trade ETH</label>
              <input
                type="number"
                min="0.01"
                max="5"
                step="0.01"
                value={autoTradingConfig.max_trade_amount_eth}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, max_trade_amount_eth: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-300 mb-1">Daily Limit</label>
              <input
                type="number"
                min="1"
                max="20"
                value={autoTradingConfig.max_daily_trades}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, max_daily_trades: parseInt(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1">Max Slippage %</label>
              <input
                type="number"
                min="1"
                max="25"
                value={autoTradingConfig.max_slippage_percent}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, max_slippage_percent: parseInt(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-300 mb-1">Min Safety Score</label>
              <input
                type="number"
                min="5"
                max="10"
                step="0.1"
                value={autoTradingConfig.min_safety_score}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, min_safety_score: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-300 mb-1">Min Profit Score</label>
              <input
                type="number"
                min="5"
                max="10"
                step="0.1"
                value={autoTradingConfig.min_profit_score}
                onChange={(e) => setAutoTradingConfig({...autoTradingConfig, min_profit_score: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
            </div>
          </div>

          <button
            onClick={setupAutoTrading}
            disabled={loading || (!autoTradingConfig.solana_wallet && !autoTradingConfig.ethereum_wallet)}
            className="w-full px-4 py-2 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all duration-200"
          >
            {loading ? 'Setting up...' : '🤖 Setup Multi-Chain Automation'}
          </button>

          {/* Safety Information */}
          <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-400/20">
            <h5 className="text-blue-300 font-medium mb-2">🛡️ Safety Features</h5>
            <ul className="text-blue-200 text-xs space-y-1">
              <li>• Maximum spending limits prevent large losses</li>
              <li>• Safety score filters reject risky tokens</li>
              <li>• Daily trade limits control frequency</li>
              <li>• Emergency stop available anytime</li>
              <li>• No private keys stored or transmitted</li>
            </ul>
          </div>
        </>
      ) : (
        <div className="space-y-3">
          <div className="p-3 bg-green-500/10 rounded-lg border border-green-400/20">
            <p className="text-green-300 text-sm font-medium">✅ Smart Contract Automation Active</p>
            <p className="text-green-200 text-xs">Wallet: {tradingStatus.wallet_balance}</p>
            <p className="text-green-200 text-xs">Daily Trades: {tradingStatus.daily_trades}</p>
            <p className="text-green-200 text-xs">Active Positions: {tradingStatus.active_positions}</p>
          </div>
          
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={emergencyStop}
              className="px-3 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg hover:from-red-700 hover:to-red-800 font-medium transition-all duration-200 text-sm"
            >
              🚨 Emergency Stop
            </button>
            
            <button
              onClick={revokePermissions}
              className="px-3 py-2 bg-gradient-to-r from-gray-600 to-gray-700 text-white rounded-lg hover:from-gray-700 hover:to-gray-800 font-medium transition-all duration-200 text-sm"
            >
              🔒 Revoke All
            </button>
          </div>

          {/* Current Settings */}
          {tradingStatus.safety_settings && (
            <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-400/20">
              <p className="text-purple-300 text-sm font-medium">⚙️ Current Settings</p>
              <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-purple-200">
                <p>Max Trade: {tradingStatus.safety_settings.max_trade_amount}</p>
                <p>Min Safety: {tradingStatus.safety_settings.min_safety_score}/10</p>
                <p>Min Profit: {tradingStatus.safety_settings.min_profit_score}/10</p>
                <p>Max Slippage: {tradingStatus.safety_settings.max_slippage}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AutomationInterface;