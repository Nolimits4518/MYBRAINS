import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { 
  Play, 
  Square, 
  Settings, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Activity,
  Wifi,
  WifiOff,
  MessageCircle,
  BarChart3
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [botStatus, setBotStatus] = useState({
    running: false,
    current_price: 0,
    rsi_value: 50,
    position: null,
    daily_pnl: 0,
    total_trades: 0,
    winning_trades: 0,
    market_data_connected: false,
    last_update: null
  });

  const [config, setConfig] = useState({
    symbol: 'ETHUSD',
    rsi_length: 14,
    stop_loss_pct: 1.0,
    take_profit_pct: 2.0,
    position_size: 0.1,
    enable_grid_tp: true
  });

  const [trades, setTrades] = useState([]);
  const [priceHistory, setPriceHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // Fetch bot status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/bot/status`);
        if (response.data.status === 'success') {
          setBotStatus(response.data.data);
          
          // Update price history for chart
          if (response.data.data.current_price > 0) {
            setPriceHistory(prev => {
              const newData = [...prev, {
                time: new Date().toLocaleTimeString(),
                price: response.data.data.current_price,
                rsi: response.data.data.rsi_value
              }];
              return newData.slice(-20); // Keep last 20 points
            });
          }
        }
      } catch (error) {
        console.error('Error fetching bot status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  // Fetch trades history
  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/trades/history`);
        if (response.data.status === 'success') {
          setTrades(response.data.data);
        }
      } catch (error) {
        console.error('Error fetching trades:', error);
      }
    };

    fetchTrades();
  }, []);

  const startBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/start`, config);
      if (response.data.status === 'success') {
        console.log('Bot started successfully');
      }
    } catch (error) {
      console.error('Error starting bot:', error);
      alert('Error starting bot: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/stop`);
      if (response.data.status === 'success') {
        console.log('Bot stopped successfully');
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
      alert('Error stopping bot: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const testTelegram = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/telegram/test`);
      if (response.data.status === 'success') {
        alert('Telegram test message sent successfully!');
      }
    } catch (error) {
      console.error('Error testing Telegram:', error);
      alert('Error testing Telegram: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const updateConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/config`, config);
      if (response.data.status === 'success') {
        alert('Configuration updated successfully!');
        setShowConfig(false);
      }
    } catch (error) {
      console.error('Error updating config:', error);
      alert('Error updating config: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value.toFixed(2)}%`;
  };

  const winRate = botStatus.total_trades > 0 ? (botStatus.winning_trades / botStatus.total_trades) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">RSI Trading Bot</h1>
              <div className="flex items-center space-x-2">
                {botStatus.market_data_connected ? (
                  <div className="flex items-center text-green-400">
                    <Wifi className="w-4 h-4 mr-1" />
                    <span className="text-sm">Connected</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-400">
                    <WifiOff className="w-4 h-4 mr-1" />
                    <span className="text-sm">Disconnected</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={testTelegram}
                disabled={loading}
                className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                Test Telegram
              </button>
              
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </button>
              
              {botStatus.running ? (
                <button
                  onClick={stopBot}
                  disabled={loading}
                  className="flex items-center px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Square className="w-4 h-4 mr-2" />
                  Stop Bot
                </button>
              ) : (
                <button
                  onClick={startBot}
                  disabled={loading}
                  className="flex items-center px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Start Bot
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Configuration Panel */}
        {showConfig && (
          <div className="mb-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Bot Configuration</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Symbol</label>
                <select
                  value={config.symbol}
                  onChange={(e) => setConfig({...config, symbol: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="ETHUSD">ETHUSD</option>
                  <option value="BTCUSD">BTCUSD</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">RSI Length</label>
                <input
                  type="number"
                  value={config.rsi_length}
                  onChange={(e) => setConfig({...config, rsi_length: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Stop Loss %</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.stop_loss_pct}
                  onChange={(e) => setConfig({...config, stop_loss_pct: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Take Profit %</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.take_profit_pct}
                  onChange={(e) => setConfig({...config, take_profit_pct: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Position Size</label>
                <input
                  type="number"
                  step="0.01"
                  value={config.position_size}
                  onChange={(e) => setConfig({...config, position_size: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="grid_tp"
                  checked={config.enable_grid_tp}
                  onChange={(e) => setConfig({...config, enable_grid_tp: e.target.checked})}
                  className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="grid_tp" className="ml-2 text-sm font-medium">Enable Grid Take Profit</label>
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={updateConfig}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
              >
                Save Configuration
              </button>
            </div>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {/* Bot Status */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Bot Status</p>
                <p className={`text-2xl font-bold ${botStatus.running ? 'text-green-400' : 'text-red-400'}`}>
                  {botStatus.running ? 'RUNNING' : 'STOPPED'}
                </p>
              </div>
              <Activity className={`w-8 h-8 ${botStatus.running ? 'text-green-400' : 'text-gray-500'}`} />
            </div>
          </div>

          {/* Current Price */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">{config.symbol} Price</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(botStatus.current_price)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          {/* RSI Value */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">RSI (14)</p>
                <p className={`text-2xl font-bold ${
                  botStatus.rsi_value > 70 ? 'text-red-400' : 
                  botStatus.rsi_value < 30 ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {botStatus.rsi_value.toFixed(1)}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          {/* Daily P&L */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Daily P&L</p>
                <p className={`text-2xl font-bold ${botStatus.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatCurrency(botStatus.daily_pnl)}
                </p>
              </div>
              {botStatus.daily_pnl >= 0 ? (
                <TrendingUp className="w-8 h-8 text-green-400" />
              ) : (
                <TrendingDown className="w-8 h-8 text-red-400" />
              )}
            </div>
          </div>
        </div>

        {/* Charts and Position Info */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Price Chart */}
          <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Price & RSI Chart</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={priceHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis yAxisId="price" orientation="left" stroke="#9CA3AF" />
                <YAxis yAxisId="rsi" orientation="right" domain={[0, 100]} stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }} 
                />
                <Line yAxisId="price" type="monotone" dataKey="price" stroke="#3B82F6" strokeWidth={2} dot={false} />
                <Line yAxisId="rsi" type="monotone" dataKey="rsi" stroke="#8B5CF6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Current Position */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Current Position</h2>
            {botStatus.position ? (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Side:</span>
                  <span className={`font-semibold ${
                    botStatus.position.side === 'LONG' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {botStatus.position.side}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Entry Price:</span>
                  <span>{formatCurrency(botStatus.position.entry_price)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Quantity:</span>
                  <span>{botStatus.position.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Stop Loss:</span>
                  <span>{formatCurrency(botStatus.position.stop_loss)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Take Profit:</span>
                  <span>{formatCurrency(botStatus.position.take_profit)}</span>
                </div>
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">No active position</p>
            )}
          </div>
        </div>

        {/* Trading Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
            <h3 className="text-lg font-medium mb-2">Total Trades</h3>
            <p className="text-3xl font-bold text-blue-400">{botStatus.total_trades}</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
            <h3 className="text-lg font-medium mb-2">Winning Trades</h3>
            <p className="text-3xl font-bold text-green-400">{botStatus.winning_trades}</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
            <h3 className="text-lg font-medium mb-2">Win Rate</h3>
            <p className="text-3xl font-bold text-yellow-400">{formatPercent(winRate)}</p>
          </div>
        </div>

        {/* Recent Trades */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Recent Trades</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-2 text-gray-400">Time</th>
                  <th className="text-left p-2 text-gray-400">Action</th>
                  <th className="text-left p-2 text-gray-400">Symbol</th>
                  <th className="text-left p-2 text-gray-400">Price</th>
                  <th className="text-left p-2 text-gray-400">Reason</th>
                </tr>
              </thead>
              <tbody>
                {trades.length > 0 ? trades.map((trade, index) => (
                  <tr key={index} className="border-b border-gray-700">
                    <td className="p-2">{new Date(trade.timestamp).toLocaleTimeString()}</td>
                    <td className="p-2">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.action === 'buy' ? 'bg-green-800 text-green-200' : 
                        trade.action === 'sell' ? 'bg-red-800 text-red-200' :
                        'bg-blue-800 text-blue-200'
                      }`}>
                        {trade.action.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-2">{trade.symbol}</td>
                    <td className="p-2">{formatCurrency(trade.price)}</td>
                    <td className="p-2 text-gray-400">{trade.reason}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-gray-400">
                      No trades recorded yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;