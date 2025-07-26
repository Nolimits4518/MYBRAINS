import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Select from 'react-select';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  ReferenceLine,
  Scatter,
  ScatterChart
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
  BarChart3,
  Clock,
  Target,
  PieChart,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Custom select styles
const selectStyles = {
  control: (styles) => ({
    ...styles,
    backgroundColor: '#374151',
    borderColor: '#4B5563',
    color: '#ffffff',
    minHeight: '40px',
    '&:hover': {
      borderColor: '#3B82F6'
    }
  }),
  option: (styles, { isFocused, isSelected }) => ({
    ...styles,
    backgroundColor: isSelected ? '#3B82F6' : isFocused ? '#4B5563' : '#374151',
    color: '#ffffff',
    '&:active': {
      backgroundColor: '#3B82F6'
    }
  }),
  menu: (styles) => ({
    ...styles,
    backgroundColor: '#374151',
    border: '1px solid #4B5563'
  }),
  singleValue: (styles) => ({
    ...styles,
    color: '#ffffff'
  }),
  placeholder: (styles) => ({
    ...styles,
    color: '#9CA3AF'
  }),
  input: (styles) => ({
    ...styles,
    color: '#ffffff'
  })
};

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
    last_update: null,
    current_symbol: 'ETHUSD',
    current_timeframe: '1h',
    available_cryptos: []
  });

  const [config, setConfig] = useState({
    symbol: 'ETHUSD',
    timeframe: '1h',
    rsi_length: 14,
    stop_loss_pct: 1.0,
    take_profit_pct: 2.0,
    position_size: 0.1,
    enable_grid_tp: true
  });

  const [cryptoList, setCryptoList] = useState([]);
  const [timeframes, setTimeframes] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [selectedTab, setSelectedTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  // Fetch bot status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/bot/status`);
        if (response.data.status === 'success') {
          setBotStatus(response.data.data);
        }
      } catch (error) {
        console.error('Error fetching bot status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch crypto list and timeframes
  useEffect(() => {
    const fetchStaticData = async () => {
      try {
        // Fetch crypto list
        const cryptoResponse = await axios.get(`${BACKEND_URL}/api/crypto/list`);
        if (cryptoResponse.data.status === 'success') {
          const cryptos = cryptoResponse.data.data.map(crypto => ({
            value: `${crypto.symbol}USD`,
            label: `${crypto.symbol} - ${crypto.name}`,
            data: crypto
          }));
          setCryptoList(cryptos);
        }

        // Fetch timeframes
        const timeframeResponse = await axios.get(`${BACKEND_URL}/api/crypto/timeframes`);
        if (timeframeResponse.data.status === 'success') {
          const tf = timeframeResponse.data.data.map(tf => ({
            value: tf.value,
            label: tf.label,
            minutes: tf.minutes
          }));
          setTimeframes(tf);
        }
      } catch (error) {
        console.error('Error fetching static data:', error);
      }
    };

    fetchStaticData();
  }, []);

  // Fetch chart data
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/analytics/chart-data/${config.symbol}?timeframe=${config.timeframe}`
        );
        if (response.data.status === 'success') {
          const formattedData = response.data.data.map(candle => ({
            ...candle,
            time: new Date(candle.timestamp).toLocaleTimeString(),
            date: new Date(candle.timestamp).toLocaleDateString(),
            fullTime: new Date(candle.timestamp),
            // Add trade markers
            buySignal: candle.trades?.some(t => t.action === 'buy') ? candle.close : null,
            sellSignal: candle.trades?.some(t => t.action === 'sell') ? candle.close : null
          }));
          setChartData(formattedData);
        }
      } catch (error) {
        console.error('Error fetching chart data:', error);
      }
    };

    if (config.symbol && config.timeframe) {
      fetchChartData();
    }
  }, [config.symbol, config.timeframe]);

  // Fetch metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get(
          `${BACKEND_URL}/api/analytics/metrics/${config.symbol}?timeframe=${config.timeframe}`
        );
        if (response.data.status === 'success') {
          setMetrics(response.data.data);
        }
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    if (config.symbol && config.timeframe) {
      fetchMetrics();
    }
  }, [config.symbol, config.timeframe, botStatus.total_trades]);

  const startBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/start`, config);
      if (response.data.status === 'success') {
        console.log('Enhanced bot started successfully');
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
        alert('Enhanced Telegram test message sent successfully!');
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
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value.toFixed(2)}%`;
  };

  const winRate = metrics?.win_rate || 0;

  const renderPriceChart = () => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2" />
        Price Chart & Signals - {config.symbol} ({config.timeframe})
      </h2>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="time" 
            stroke="#9CA3AF" 
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis stroke="#9CA3AF" domain={['dataMin - 10', 'dataMax + 10']} />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1F2937', 
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#ffffff'
            }} 
            labelFormatter={(value) => `Time: ${value}`}
            formatter={(value, name) => [
              typeof value === 'number' ? formatCurrency(value) : value,
              name
            ]}
          />
          
          {/* Price line */}
          <Line 
            type="monotone" 
            dataKey="close" 
            stroke="#3B82F6" 
            strokeWidth={2} 
            dot={false} 
            name="Price"
          />
          
          {/* Buy signals */}
          <Line 
            type="monotone" 
            dataKey="buySignal" 
            stroke="#10B981" 
            strokeWidth={0} 
            dot={{ fill: '#10B981', strokeWidth: 2, r: 6 }}
            connectNulls={false}
            name="Buy Signal"
          />
          
          {/* Sell signals */}
          <Line 
            type="monotone" 
            dataKey="sellSignal" 
            stroke="#EF4444" 
            strokeWidth={0} 
            dot={{ fill: '#EF4444', strokeWidth: 2, r: 6 }}
            connectNulls={false}
            name="Sell Signal"
          />
          
          {/* Current position reference line */}
          {botStatus.position && (
            <ReferenceLine 
              y={botStatus.position.entry_price} 
              stroke={botStatus.position.side === 'LONG' ? '#10B981' : '#EF4444'}
              strokeDasharray="5 5"
              label={{ value: `Entry: ${formatCurrency(botStatus.position.entry_price)}`, position: 'right' }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );

  const renderRSIChart = () => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h2 className="text-xl font-semibold mb-4">RSI Indicator</h2>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="time" stroke="#9CA3AF" />
          <YAxis domain={[0, 100]} stroke="#9CA3AF" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1F2937', 
              border: '1px solid #374151',
              borderRadius: '8px'
            }} 
          />
          
          {/* RSI zones */}
          <ReferenceLine y={70} stroke="#EF4444" strokeDasharray="3 3" />
          <ReferenceLine y={30} stroke="#10B981" strokeDasharray="3 3" />
          <ReferenceLine y={50} stroke="#6B7280" strokeDasharray="1 1" />
          
          <Line 
            type="monotone" 
            dataKey="rsi" 
            stroke="#8B5CF6" 
            strokeWidth={2} 
            dot={false}
            name="RSI"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  const renderPositionDetails = () => {
    if (!botStatus.position) {
      return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Current Position</h2>
          <div className="text-center py-8 text-gray-400">
            <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No active position</p>
          </div>
        </div>
      );
    }

    const position = botStatus.position;
    const pnlColor = position.pnl >= 0 ? 'text-green-400' : 'text-red-400';
    const sideColor = position.side === 'LONG' ? 'text-green-400' : 'text-red-400';

    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Current Position</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Side:</span>
              <span className={`font-semibold ${sideColor}`}>{position.side}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Entry Price:</span>
              <span className="text-white">{formatCurrency(position.entry_price)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Current Price:</span>
              <span className="text-white">{formatCurrency(position.current_price)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Quantity:</span>
              <span className="text-white">{position.quantity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Timeframe:</span>
              <span className="text-blue-400">{position.timeframe}</span>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">P&L:</span>
              <span className={`font-semibold ${pnlColor}`}>{formatCurrency(position.pnl)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">P&L %:</span>
              <span className={`font-semibold ${pnlColor}`}>{formatPercent(position.pnl_pct)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Stop Loss:</span>
              <span className="text-red-400">{formatCurrency(position.stop_loss)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Take Profit:</span>
              <span className="text-green-400">{formatCurrency(position.take_profit)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Entry Time:</span>
              <span className="text-white text-sm">{new Date(position.entry_time).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Total Trades</p>
            <p className="text-2xl font-bold text-blue-400">{metrics?.total_trades || 0}</p>
          </div>
          <BarChart3 className="w-8 h-8 text-blue-400" />
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Win Rate</p>
            <p className="text-2xl font-bold text-green-400">{formatPercent(winRate)}</p>
          </div>
          <Target className="w-8 h-8 text-green-400" />
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Total P&L</p>
            <p className={`text-2xl font-bold ${metrics?.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {formatCurrency(metrics?.total_pnl || 0)}
            </p>
          </div>
          {(metrics?.total_pnl || 0) >= 0 ? (
            <TrendingUp className="w-8 h-8 text-green-400" />
          ) : (
            <TrendingDown className="w-8 h-8 text-red-400" />
          )}
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-400">Avg Profit</p>
            <p className="text-2xl font-bold text-yellow-400">
              {formatCurrency(metrics?.average_profit || 0)}
            </p>
          </div>
          <DollarSign className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Enhanced RSI Trading Bot</h1>
              <div className="flex items-center space-x-4">
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
                <div className="flex items-center text-blue-400 text-sm">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>{config.timeframe}</span>
                </div>
                <div className="text-gray-400 text-sm">
                  {cryptoList.length} Cryptos
                </div>
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
            <h2 className="text-xl font-semibold mb-4">Enhanced Bot Configuration</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Cryptocurrency</label>
                <Select
                  value={cryptoList.find(c => c.value === config.symbol)}
                  onChange={(selectedOption) => setConfig({...config, symbol: selectedOption.value})}
                  options={cryptoList}
                  styles={selectStyles}
                  placeholder="Select cryptocurrency..."
                  isSearchable={true}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Timeframe</label>
                <Select
                  value={timeframes.find(tf => tf.value === config.timeframe)}
                  onChange={(selectedOption) => setConfig({...config, timeframe: selectedOption.value})}
                  options={timeframes}
                  styles={selectStyles}
                  placeholder="Select timeframe..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">RSI Length</label>
                <input
                  type="number"
                  value={config.rsi_length}
                  onChange={(e) => setConfig({...config, rsi_length: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Stop Loss %</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.stop_loss_pct}
                  onChange={(e) => setConfig({...config, stop_loss_pct: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Take Profit %</label>
                <input
                  type="number"
                  step="0.1"
                  value={config.take_profit_pct}
                  onChange={(e) => setConfig({...config, take_profit_pct: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Position Size</label>
                <input
                  type="number"
                  step="0.01"
                  value={config.position_size}
                  onChange={(e) => setConfig({...config, position_size: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 text-white"
                />
              </div>
            </div>
            
            <div className="mt-4 flex items-center">
              <input
                type="checkbox"
                id="grid_tp"
                checked={config.enable_grid_tp}
                onChange={(e) => setConfig({...config, enable_grid_tp: e.target.checked})}
                className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
              />
              <label htmlFor="grid_tp" className="ml-2 text-sm font-medium">Enable Grid Take Profit</label>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowConfig(false)}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
              >
                Cancel
              </button>
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
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Bot Status</p>
                <p className={`text-2xl font-bold ${botStatus.running ? 'text-green-400' : 'text-red-400'}`}>
                  {botStatus.running ? 'RUNNING' : 'STOPPED'}
                </p>
                <p className="text-xs text-gray-500">{config.symbol} • {config.timeframe}</p>
              </div>
              <Activity className={`w-8 h-8 ${botStatus.running ? 'text-green-400' : 'text-gray-500'}`} />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">{config.symbol} Price</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(botStatus.current_price)}
                </p>
                <p className="text-xs text-gray-500">Real-time</p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">RSI ({config.rsi_length})</p>
                <p className={`text-2xl font-bold ${
                  botStatus.rsi_value > 70 ? 'text-red-400' : 
                  botStatus.rsi_value < 30 ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {botStatus.rsi_value.toFixed(1)}
                </p>
                <p className="text-xs text-gray-500">
                  {botStatus.rsi_value > 70 ? 'Overbought' : 
                   botStatus.rsi_value < 30 ? 'Oversold' : 'Neutral'}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Daily P&L</p>
                <p className={`text-2xl font-bold ${botStatus.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {formatCurrency(botStatus.daily_pnl)}
                </p>
                <p className="text-xs text-gray-500">
                  {botStatus.total_trades} trades
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

        {/* Navigation Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {['dashboard', 'charts', 'position', 'analytics'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setSelectedTab(tab)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                    selectedTab === tab
                      ? 'border-blue-500 text-blue-500'
                      : 'border-transparent text-gray-400 hover:text-gray-300'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {selectedTab === 'dashboard' && (
          <div className="space-y-6">
            {renderMetrics()}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {renderPriceChart()}
              {renderPositionDetails()}
            </div>
          </div>
        )}

        {selectedTab === 'charts' && (
          <div className="space-y-6">
            {renderPriceChart()}
            {renderRSIChart()}
          </div>
        )}

        {selectedTab === 'position' && (
          <div className="space-y-6">
            {renderPositionDetails()}
            {renderMetrics()}
          </div>
        )}

        {selectedTab === 'analytics' && (
          <div className="space-y-6">
            {renderMetrics()}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-xl font-semibold mb-4">Detailed Analytics</h2>
              {metrics ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-medium mb-3">Trade Statistics</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Symbol:</span>
                        <span className="text-white">{metrics.symbol}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Timeframe:</span>
                        <span className="text-white">{metrics.timeframe}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Total Trades:</span>
                        <span className="text-white">{metrics.total_trades}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Winning Trades:</span>
                        <span className="text-green-400">{metrics.winning_trades}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Losing Trades:</span>
                        <span className="text-red-400">{metrics.losing_trades}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="text-lg font-medium mb-3">Performance Metrics</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Win Rate:</span>
                        <span className="text-yellow-400">{formatPercent(metrics.win_rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Total P&L:</span>
                        <span className={metrics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                          {formatCurrency(metrics.total_pnl)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Profit:</span>
                        <span className="text-green-400">{formatCurrency(metrics.average_profit)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Avg Loss:</span>
                        <span className="text-red-400">{formatCurrency(metrics.average_loss)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-400 py-8">No trading data available yet</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;