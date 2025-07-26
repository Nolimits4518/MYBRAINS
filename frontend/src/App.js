import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import Select from 'react-select';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ComposedChart,
  Bar,
  ReferenceLine,
  Area,
  AreaChart
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
  CheckCircle,
  Zap,
  Shield,
  Eye,
  Cpu,
  Radio,
  Globe,
  Flame,
  Star,
  Hexagon,
  Link2
} from 'lucide-react';
import PlatformConnector from './components/PlatformConnector';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// 🌟 Particle Component for Background Effects
const ParticleField = () => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    for (let i = 0; i < 50; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 2,
        opacity: Math.random() * 0.5 + 0.2
      });
    }
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      particles.forEach(particle => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;
        
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 245, 255, ${particle.opacity})`;
        ctx.fill();
      });
      
      requestAnimationFrame(animate);
    };
    
    animate();
    
    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return <canvas ref={canvasRef} className="fixed top-0 left-0 pointer-events-none z-0" />;
};

// 🎯 Holographic Status Indicator
const StatusIndicator = ({ status, label, icon: Icon }) => {
  const statusConfig = {
    online: { color: 'text-green-400', glow: 'shadow-green-400/50', pulse: 'animate-pulse' },
    offline: { color: 'text-red-400', glow: 'shadow-red-400/50', pulse: '' },
    warning: { color: 'text-yellow-400', glow: 'shadow-yellow-400/50', pulse: 'animate-pulse' }
  };
  
  const config = statusConfig[status] || statusConfig.offline;
  
  return (
    <div className="flex items-center space-x-2">
      <div className={`p-1 rounded-full ${config.color} ${config.glow} ${config.pulse}`}>
        <Icon className="w-4 h-4" />
      </div>
      <span className={`text-sm font-mono ${config.color} text-glow`}>{label}</span>
    </div>
  );
};

// 🌊 Animated Waveform Component
const Waveform = ({ active = false }) => {
  const bars = Array.from({ length: 5 }, (_, i) => i);
  
  return (
    <div className="waveform">
      {bars.map((bar) => (
        <motion.div
          key={bar}
          className="wave-bar"
          animate={active ? {
            height: [10, 40, 10],
            opacity: [0.5, 1, 0.5]
          } : {
            height: 10,
            opacity: 0.3
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: bar * 0.1
          }}
        />
      ))}
    </div>
  );
};

// 💎 3D Metric Card Component
const MetricCard = ({ title, value, change, icon: Icon, type = 'default' }) => {
  const typeConfig = {
    default: 'border-cyan-400/30 bg-gradient-to-br from-cyan-500/10 to-pink-500/10',
    success: 'border-green-400/30 bg-gradient-to-br from-green-500/10 to-cyan-500/10',
    danger: 'border-red-400/30 bg-gradient-to-br from-red-500/10 to-pink-500/10',
    warning: 'border-yellow-400/30 bg-gradient-to-br from-yellow-500/10 to-orange-500/10'
  };
  
  return (
    <motion.div
      className={`holo-card p-6 ${typeConfig[type]}`}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="metric-label">{title}</div>
        <Icon className="w-6 h-6 text-cyan-400" />
      </div>
      <div className="metric-value">{value}</div>
      {change && (
        <div className={`text-sm font-mono mt-2 flex items-center ${
          change.startsWith('+') ? 'text-green-400' : 
          change.startsWith('-') ? 'text-red-400' : 'text-yellow-400'
        }`}>
          {change.startsWith('+') ? <TrendingUp className="w-3 h-3 mr-1" /> :
           change.startsWith('-') ? <TrendingDown className="w-3 h-3 mr-1" /> : null}
          {change}
        </div>
      )}
    </motion.div>
  );
};

// 🎨 Custom Select Styles for Cyberpunk Theme
const cyberSelectStyles = {
  control: (styles, { isFocused }) => ({
    ...styles,
    backgroundColor: 'rgba(20, 25, 40, 0.8)',
    borderColor: isFocused ? '#00F5FF' : 'rgba(0, 245, 255, 0.3)',
    color: '#E0E6ED',
    minHeight: '40px',
    boxShadow: isFocused ? '0 0 20px rgba(0, 245, 255, 0.3)' : 'none',
    backdropFilter: 'blur(10px)',
    '&:hover': {
      borderColor: '#00F5FF'
    }
  }),
  option: (styles, { isFocused, isSelected }) => ({
    ...styles,
    backgroundColor: isSelected ? '#00F5FF' : isFocused ? 'rgba(0, 245, 255, 0.1)' : 'rgba(20, 25, 40, 0.9)',
    color: isSelected ? '#0A0A0F' : '#E0E6ED',
    '&:active': {
      backgroundColor: 'rgba(0, 245, 255, 0.2)'
    }
  }),
  menu: (styles) => ({
    ...styles,
    backgroundColor: 'rgba(20, 25, 40, 0.95)',
    border: '1px solid rgba(0, 245, 255, 0.3)',
    backdropFilter: 'blur(20px)',
    boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)'
  }),
  singleValue: (styles) => ({
    ...styles,
    color: '#E0E6ED'
  }),
  placeholder: (styles) => ({
    ...styles,
    color: 'rgba(224, 230, 237, 0.5)'
  }),
  input: (styles) => ({
    ...styles,
    color: '#E0E6ED'
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
  const [selectedTab, setSelectedTab] = useState('neural-core');
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Add notification system
  const addNotification = useCallback((type, message) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  }, []);

  // Fetch bot status with enhanced error handling
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/bot/status`);
        if (response.data.status === 'success') {
          setBotStatus(prev => ({
            ...prev,
            ...response.data.data
          }));
        }
      } catch (error) {
        console.error('Error fetching bot status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  // Fetch static data (crypto list and timeframes)
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

  // Enhanced bot control functions
  const startBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/start`, config);
      if (response.data.status === 'success') {
        addNotification('success', '🚀 Neural RSI System Activated');
      }
    } catch (error) {
      console.error('Error starting bot:', error);
      addNotification('error', '❌ System Activation Failed');
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/bot/stop`);
      if (response.data.status === 'success') {
        addNotification('warning', '⏹️ Neural RSI System Deactivated');
      }
    } catch (error) {
      console.error('Error stopping bot:', error);
      addNotification('error', '❌ System Deactivation Failed');
    } finally {
      setLoading(false);
    }
  };

  const testTelegram = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${BACKEND_URL}/api/telegram/test`);
      if (response.data.status === 'success') {
        addNotification('success', '📡 Quantum Communication Link Established');
      }
    } catch (error) {
      console.error('Error testing Telegram:', error);
      addNotification('error', '❌ Communication Link Failed');
    } finally {
      setLoading(false);
    }
  };

  // Quick symbol/timeframe switchers
  const quickSwitchSymbol = async (newSymbol) => {
    setConfig({...config, symbol: newSymbol});
    if (botStatus.running) {
      await stopBot();
      setTimeout(() => startBot(), 1000);
    }
  };

  const quickSwitchTimeframe = async (newTimeframe) => {
    setConfig({...config, timeframe: newTimeframe});
    if (botStatus.running) {
      await stopBot();
      setTimeout(() => startBot(), 1000);
    }
  };

  // Utility functions
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);
  };

  const formatPercent = (value) => `${value.toFixed(2)}%`;
  const winRate = metrics?.win_rate || 0;

  // Enhanced Chart Component
  const renderNeuralChart = () => (
    <motion.div 
      className="holo-card p-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="section-title flex items-center">
          <Hexagon className="w-5 h-5 mr-2" />
          Quantum Price Matrix
        </h3>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-cyan-400 font-mono">{config.symbol}</span>
          <span className="text-xs text-pink-400 font-mono">{config.timeframe}</span>
          <Waveform active={botStatus.running} />
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00F5FF" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#00F5FF" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 245, 255, 0.1)" />
          <XAxis 
            dataKey="time" 
            stroke="rgba(224, 230, 237, 0.5)" 
            fontSize={10}
            fontFamily="JetBrains Mono"
          />
          <YAxis 
            stroke="rgba(224, 230, 237, 0.5)" 
            fontSize={10}
            fontFamily="JetBrains Mono"
          />
          
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'rgba(20, 25, 40, 0.95)', 
              border: '1px solid rgba(0, 245, 255, 0.3)',
              borderRadius: '8px',
              color: '#E0E6ED',
              backdropFilter: 'blur(10px)'
            }} 
          />
          
          <Area 
            type="monotone" 
            dataKey="close" 
            stroke="#00F5FF" 
            strokeWidth={2}
            fill="url(#priceGradient)"
            fillOpacity={0.6}
          />
          
          {/* Buy signals */}
          <Line 
            type="monotone" 
            dataKey="buySignal" 
            stroke="#39FF14" 
            strokeWidth={0} 
            dot={{ fill: '#39FF14', strokeWidth: 2, r: 8, filter: 'drop-shadow(0 0 6px #39FF14)' }}
            connectNulls={false}
          />
          
          {/* Sell signals */}
          <Line 
            type="monotone" 
            dataKey="sellSignal" 
            stroke="#FF073A" 
            strokeWidth={0} 
            dot={{ fill: '#FF073A', strokeWidth: 2, r: 8, filter: 'drop-shadow(0 0 6px #FF073A)' }}
            connectNulls={false}
          />
          
          {/* Position entry line */}
          {botStatus.position && (
            <ReferenceLine 
              y={botStatus.position.entry_price} 
              stroke={botStatus.position.side === 'LONG' ? '#39FF14' : '#FF073A'}
              strokeDasharray="5 5"
              strokeWidth={2}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </motion.div>
  );

  // Tab Navigation Component
  const TabButton = ({ id, label, icon: Icon, active, onClick }) => (
    <motion.button
      onClick={() => onClick(id)}
      className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-mono text-sm transition-all ${
        active 
          ? 'bg-gradient-to-r from-cyan-500/20 to-pink-500/20 border border-cyan-400/50 text-cyan-400' 
          : 'border border-transparent text-gray-400 hover:text-cyan-400 hover:border-cyan-400/30'
      }`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
    </motion.button>
  );

  return (
    <div className="min-h-screen text-white relative">
      {/* Background Particle Field */}
      <ParticleField />
      
      {/* Notification System */}
      <AnimatePresence>
        {notifications.map((notification) => (
          <motion.div
            key={notification.id}
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            className={`fixed top-4 right-4 z-50 p-4 rounded-lg border backdrop-blur-lg ${
              notification.type === 'success' ? 'bg-green-500/10 border-green-400/30 text-green-400' :
              notification.type === 'error' ? 'bg-red-500/10 border-red-400/30 text-red-400' :
              'bg-yellow-500/10 border-yellow-400/30 text-yellow-400'
            }`}
          >
            {notification.message}
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Cyberpunk Header */}
      <header className="cyber-header sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <motion.div 
              className="flex items-center space-x-4"
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="relative">
                <Cpu className="w-10 h-10 text-cyan-400 animate-pulse" />
                <div className="absolute inset-0 animate-ping">
                  <Cpu className="w-10 h-10 text-cyan-400/20" />
                </div>
              </div>
              <div>
                <h1 className="cyber-title text-2xl">
                  <span className="glitch" data-text="NEURAL RSI SYSTEM">NEURAL RSI SYSTEM</span>
                </h1>
                <div className="flex items-center space-x-4 mt-1">
                  <StatusIndicator 
                    status={botStatus.market_data_connected ? 'online' : 'offline'} 
                    label="QUANTUM LINK" 
                    icon={Radio} 
                  />
                  <StatusIndicator 
                    status={botStatus.running ? 'online' : 'offline'} 
                    label="NEURAL CORE" 
                    icon={Zap} 
                  />
                  <span className="text-xs text-gray-400 font-mono">
                    v2.0 | {cryptoList.length} ASSETS
                  </span>
                </div>
              </div>
            </motion.div>

            {/* Quick Controls */}
            <motion.div 
              className="flex items-center space-x-4"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
            >
              {/* Quick Symbol Selector */}
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-cyan-400" />
                <Select
                  value={cryptoList.find(c => c.value === config.symbol)}
                  onChange={(option) => quickSwitchSymbol(option.value)}
                  options={cryptoList.slice(0, 20)}
                  styles={cyberSelectStyles}
                  className="w-40"
                  placeholder="Asset"
                />
              </div>

              {/* Quick Timeframe Selector */}
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-pink-400" />
                <Select
                  value={timeframes.find(tf => tf.value === config.timeframe)}
                  onChange={(option) => quickSwitchTimeframe(option.value)}
                  options={timeframes}
                  styles={cyberSelectStyles}
                  className="w-32"
                  placeholder="Frame"
                />
              </div>

              {/* Control Buttons */}
              <button
                onClick={testTelegram}
                disabled={loading}
                className="neon-button disabled:opacity-50"
              >
                <MessageCircle className="w-4 h-4 mr-2" />
                COMM
              </button>

              <button
                onClick={() => setShowConfig(!showConfig)}
                className="neon-button"
              >
                <Settings className="w-4 h-4 mr-2" />
                CONFIG
              </button>

              {botStatus.running ? (
                <button
                  onClick={stopBot}
                  disabled={loading}
                  className="neon-button neon-button-danger disabled:opacity-50"
                >
                  {loading ? <div className="cyber-loader w-4 h-4 mr-2" /> : <Square className="w-4 h-4 mr-2" />}
                  HALT
                </button>
              ) : (
                <button
                  onClick={startBot}
                  disabled={loading}
                  className="neon-button neon-button-success disabled:opacity-50"
                >
                  {loading ? <div className="cyber-loader w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                  ACTIVATE
                </button>
              )}
            </motion.div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8 relative z-10">
        {/* Enhanced Configuration Panel */}
        <AnimatePresence>
          {showConfig && (
            <motion.div 
              className="mb-8 holo-card p-8"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <h2 className="section-title text-2xl mb-6 flex items-center">
                <Shield className="w-6 h-6 mr-3" />
                Neural Configuration Matrix
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">QUANTUM ASSET</label>
                  <Select
                    value={cryptoList.find(c => c.value === config.symbol)}
                    onChange={(option) => setConfig({...config, symbol: option.value})}
                    options={cryptoList}
                    styles={cyberSelectStyles}
                    placeholder="Select Asset..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">TIME DIMENSION</label>
                  <Select
                    value={timeframes.find(tf => tf.value === config.timeframe)}
                    onChange={(option) => setConfig({...config, timeframe: option.value})}
                    options={timeframes}
                    styles={cyberSelectStyles}
                    placeholder="Select Frame..."
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">RSI NEURAL LENGTH</label>
                  <input
                    type="number"
                    value={config.rsi_length}
                    onChange={(e) => setConfig({...config, rsi_length: parseInt(e.target.value)})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-cyan-400/30 rounded-lg text-white font-mono focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">RISK BARRIER %</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.stop_loss_pct}
                    onChange={(e) => setConfig({...config, stop_loss_pct: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-red-400/30 rounded-lg text-white font-mono focus:border-red-400 focus:ring-1 focus:ring-red-400/30"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">PROFIT TARGET %</label>
                  <input
                    type="number"
                    step="0.1"
                    value={config.take_profit_pct}
                    onChange={(e) => setConfig({...config, take_profit_pct: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-green-400/30 rounded-lg text-white font-mono focus:border-green-400 focus:ring-1 focus:ring-green-400/30"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-mono text-cyan-400 mb-3">POSITION SIZE</label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.position_size}
                    onChange={(e) => setConfig({...config, position_size: parseFloat(e.target.value)})}
                    className="w-full px-4 py-3 bg-gray-800/50 border border-yellow-400/30 rounded-lg text-white font-mono focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400/30"
                  />
                </div>
              </div>
              
              <div className="mt-6 flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="grid_tp"
                    checked={config.enable_grid_tp}
                    onChange={(e) => setConfig({...config, enable_grid_tp: e.target.checked})}
                    className="w-5 h-5 text-cyan-400 bg-gray-800 border-cyan-400/30 rounded focus:ring-cyan-400/30"
                  />
                  <label htmlFor="grid_tp" className="ml-3 text-sm font-mono text-cyan-400">
                    ENABLE GRID MATRIX
                  </label>
                </div>
                
                <button
                  onClick={() => setShowConfig(false)}
                  className="neon-button"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  LOCK CONFIG
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Neural Status Grid */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <MetricCard
            title="NEURAL STATUS"
            value={botStatus.running ? 'ACTIVE' : 'DORMANT'}
            change={botStatus.running ? '+ONLINE' : 'OFFLINE'}
            icon={botStatus.running ? Zap : Eye}
            type={botStatus.running ? 'success' : 'danger'}
          />
          
          <MetricCard
            title={`${config.symbol} QUANTUM PRICE`}
            value={formatCurrency(botStatus.current_price)}
            change="+2.4%"
            icon={DollarSign}
            type="default"
          />
          
          <MetricCard
            title="RSI NEURAL FIELD"
            value={botStatus.rsi_value.toFixed(1)}
            change={botStatus.rsi_value > 70 ? 'OVERBOUGHT' : botStatus.rsi_value < 30 ? 'OVERSOLD' : 'NEUTRAL'}
            icon={BarChart3}
            type={botStatus.rsi_value > 70 ? 'danger' : botStatus.rsi_value < 30 ? 'success' : 'warning'}
          />
          
          <MetricCard
            title="PROFIT MATRIX"
            value={formatCurrency(botStatus.daily_pnl)}
            change={botStatus.total_trades ? `${botStatus.total_trades} TRADES` : 'NO TRADES'}
            icon={botStatus.daily_pnl >= 0 ? TrendingUp : TrendingDown}
            type={botStatus.daily_pnl >= 0 ? 'success' : 'danger'}
          />
        </motion.div>

        {/* Navigation Tabs */}
        <div className="mb-8">
          <div className="flex space-x-4 overflow-x-auto pb-2">
            <TabButton id="neural-core" label="Neural Core" icon={Cpu} active={selectedTab === 'neural-core'} onClick={setSelectedTab} />
            <TabButton id="quantum-charts" label="Quantum Charts" icon={BarChart3} active={selectedTab === 'quantum-charts'} onClick={setSelectedTab} />
            <TabButton id="position-matrix" label="Position Matrix" icon={Target} active={selectedTab === 'position-matrix'} onClick={setSelectedTab} />
            <TabButton id="platform-connector" label="Platform Connector" icon={Globe} active={selectedTab === 'platform-connector'} onClick={setSelectedTab} />
            <TabButton id="system-diagnostics" label="System Diagnostics" icon={Activity} active={selectedTab === 'system-diagnostics'} onClick={setSelectedTab} />
          </div>
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {selectedTab === 'neural-core' && (
            <motion.div
              key="neural-core"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                  {renderNeuralChart()}
                </div>
                
                <div className="holo-card p-6">
                  <h3 className="section-title mb-6 flex items-center">
                    <Target className="w-5 h-5 mr-2" />
                    Active Position
                  </h3>
                  
                  {botStatus.position ? (
                    <div className="space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Side:</span>
                        <span className={`font-bold text-lg ${
                          botStatus.position.side === 'LONG' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {botStatus.position.side}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Entry:</span>
                        <span className="font-mono text-cyan-400">
                          {formatCurrency(botStatus.position.entry_price)}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Current:</span>
                        <span className="font-mono text-white">
                          {formatCurrency(botStatus.position.current_price)}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">P&L:</span>
                        <span className={`font-mono font-bold ${
                          botStatus.position.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {formatCurrency(botStatus.position.pnl)} 
                          ({formatPercent(botStatus.position.pnl_pct)})
                        </span>
                      </div>
                      
                      <div className="mt-6 pt-4 border-t border-gray-700">
                        <div className="text-xs text-gray-400 mb-2">Grid Progress</div>
                        <div className="progress-bar-container">
                          <div className="progress-bar" style={{ width: '60%' }} />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Target className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                      <p className="text-gray-400">No Active Position</p>
                      <p className="text-xs text-gray-500 mt-2">Neural system monitoring for signals...</p>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
          
          {selectedTab === 'quantum-charts' && (
            <motion.div
              key="quantum-charts"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-8"
            >
              {renderNeuralChart()}
              
              <div className="holo-card p-6">
                <h3 className="section-title mb-4 flex items-center">
                  <Activity className="w-5 h-5 mr-2" />
                  RSI Quantum Field
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="rsiGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                    <XAxis dataKey="time" stroke="rgba(224, 230, 237, 0.5)" fontSize={10} />
                    <YAxis domain={[0, 100]} stroke="rgba(224, 230, 237, 0.5)" fontSize={10} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'rgba(20, 25, 40, 0.95)', 
                        border: '1px solid rgba(139, 92, 246, 0.3)',
                        borderRadius: '8px'
                      }} 
                    />
                    
                    <ReferenceLine y={70} stroke="#FF073A" strokeDasharray="3 3" />
                    <ReferenceLine y={30} stroke="#39FF14" strokeDasharray="3 3" />
                    <ReferenceLine y={50} stroke="rgba(224, 230, 237, 0.3)" strokeDasharray="1 1" />
                    
                    <Area 
                      type="monotone" 
                      dataKey="rsi" 
                      stroke="#8B5CF6" 
                      strokeWidth={2}
                      fill="url(#rsiGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;