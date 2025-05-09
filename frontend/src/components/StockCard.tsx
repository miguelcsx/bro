import React, { useState, useEffect } from 'react';
import './StockCard.css';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Area, AreaChart, ReferenceLine 
} from 'recharts';

interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  afterHoursPrice?: number;
  afterHoursChange?: number;
  afterHoursChangePercent?: number;
  chartData?: {
    time: string;
    price: number;
  }[];
  stats?: {
    open?: number;
    volume?: string;
    marketCap?: string;
    dayLow?: number;
    yearLow?: number;
    eps?: number;
    dayHigh?: number;
    yearHigh?: number;
    peRatio?: number;
  };
}

// Sample data for different timeframes (will be replaced with API data)
const generateSampleData = (basePrice: number, timeframe: string) => {
  const now = new Date();
  const data: {date: string, price: number}[] = [];
  const isUp = Math.random() > 0.4; // 60% chance of uptrend
  
  let points = 0;
  let timeIncrement = 0;
  
  switch(timeframe) {
    case '1D':
      points = 24;
      timeIncrement = 60 * 60 * 1000; // 1 hour
      break;
    case '5D':
      points = 5;
      timeIncrement = 24 * 60 * 60 * 1000; // 1 day
      break;
    case '1M':
      points = 30;
      timeIncrement = 24 * 60 * 60 * 1000; // 1 day
      break;
    case '6M':
      points = 6;
      timeIncrement = 30 * 24 * 60 * 60 * 1000; // 1 month
      break;
    default:
      points = 24;
      timeIncrement = 60 * 60 * 1000; // 1 hour
  }
  
  for (let i = points; i >= 0; i--) {
    const date = new Date(now.getTime() - (i * timeIncrement));
    const volatility = isUp ? 
      Math.random() * 0.03 - 0.01 : // up trend with some down moves
      Math.random() * 0.03 - 0.02;  // down trend with some up moves
    
    const trend = isUp ? 
      (i / points) * (Math.random() * 0.1) : // gradual uptrend
      (i / points) * (Math.random() * -0.1); // gradual downtrend
    
    const price = basePrice * (1 + volatility + trend);
    
    data.push({
      date: date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      price: parseFloat(price.toFixed(2))
    });
  }
  
  return data;
};

const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  changePercent,
  afterHoursPrice,
  afterHoursChange,
  afterHoursChangePercent,
  stats
}) => {
  const [timeframe, setTimeframe] = useState<string>('1D');
  const [chartData, setChartData] = useState<{date: string, price: number}[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // Determine if stock is up or down
  const isUp = change >= 0;
  const afterHoursIsUp = afterHoursChange ? afterHoursChange >= 0 : false;
  
  // Load chart data when timeframe changes
  useEffect(() => {
    setIsLoading(true);
    
    // Simulate API call delay
    const timer = setTimeout(() => {
      // In a real app, this would be an API call to get historical data
      // For now, we'll use our sample data generator
      const data = generateSampleData(price, timeframe);
      setChartData(data);
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [timeframe, price]);
  
  // Format data for display
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };
  
  // Calculate min/max for chart y-axis
  const dataMin = chartData.length > 0 ? 
    Math.min(...chartData.map(d => d.price)) : price * 0.95;
  
  const dataMax = chartData.length > 0 ? 
    Math.max(...chartData.map(d => d.price)) : price * 1.05;
  
  // Padding for y-axis to avoid chart touching boundaries
  const yAxisMin = dataMin - (dataMax - dataMin) * 0.1;
  const yAxisMax = dataMax + (dataMax - dataMin) * 0.1;
  
  // Custom tooltip for hover data
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="price">{formatCurrency(payload[0].value)}</p>
          <p className="time">{payload[0].payload.date}</p>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div className="stock-card">
      <div className="stock-header">
        <h2>{name} ({symbol})</h2>
      </div>
      
      <div className="stock-price">
        <span className="current-price">{formatCurrency(price)}</span>
        <span className={`price-change ${isUp ? 'positive' : 'negative'}`}>
          {isUp ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%) Hoy
        </span>
        
        {afterHoursPrice && (
          <div className="after-hours">
            <span className="after-hours-price">{formatCurrency(afterHoursPrice)}</span>
            <span className={`after-hours-change ${afterHoursIsUp ? 'positive' : 'negative'}`}>
              {afterHoursIsUp ? '+' : ''}{afterHoursChange?.toFixed(2)} ({afterHoursChangePercent?.toFixed(2)}%) Después de hora
            </span>
          </div>
        )}
      </div>
      
      <div className="chart-timeframes">
        {['1D', '5D', '1M', '6M', 'YTD', '1Y', '5Y', 'MAX'].map(tf => (
          <button 
            key={tf}
            className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
            onClick={() => setTimeframe(tf)}
          >
            {tf}
          </button>
        ))}
      </div>
      
      <div className="stock-chart">
        {isLoading ? (
          <div className="chart-loading">Loading chart data...</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
            >
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop 
                    offset="5%" 
                    stopColor={isUp ? "#22c55e" : "#ef4444"} 
                    stopOpacity={0.3}
                  />
                  <stop 
                    offset="95%" 
                    stopColor={isUp ? "#22c55e" : "#ef4444"} 
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 10, fill: '#aaa' }}
                tickLine={false}
                axisLine={{ stroke: '#333' }}
              />
              <YAxis 
                domain={[yAxisMin, yAxisMax]} 
                tick={{ fontSize: 10, fill: '#aaa' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={price} stroke="#888" strokeDasharray="3 3" />
              <Area 
                type="monotone" 
                dataKey="price" 
                stroke={isUp ? "#22c55e" : "#ef4444"} 
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorPrice)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
      
      {stats && (
        <div className="stock-stats">
          <div className="stats-row">
            <div className="stat-item">
              <span className="stat-label">Abrir</span>
              <span className="stat-value">{formatCurrency(stats.open || 0)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Volumen</span>
              <span className="stat-value">{stats.volume}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Capitalización de mercado</span>
              <span className="stat-value">{stats.marketCap}</span>
            </div>
          </div>
          
          <div className="stats-row">
            <div className="stat-item">
              <span className="stat-label">Mínimo del día</span>
              <span className="stat-value">{formatCurrency(stats.dayLow || 0)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Mínimo anual</span>
              <span className="stat-value">{formatCurrency(stats.yearLow || 0)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">EPS (TTM)</span>
              <span className="stat-value">{stats.eps?.toFixed(2)}</span>
            </div>
          </div>
          
          <div className="stats-row">
            <div className="stat-item">
              <span className="stat-label">Máximo del día</span>
              <span className="stat-value">{formatCurrency(stats.dayHigh || 0)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Máximo anual</span>
              <span className="stat-value">{formatCurrency(stats.yearHigh || 0)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Relación precio-ganancia</span>
              <span className="stat-value">{stats.peRatio?.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockCard; 