import React, { useState } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, Legend, ReferenceArea
} from 'recharts';
import './PredictionChart.css';

// Base interface for data points with required properties
interface DataPoint {
  date: string;
  price: number;
}

// Interface for chart data with all needed properties
interface ChartDataPoint {
  date: string;
  price?: number;
  predictedPrice?: number;
  upperBound?: number;
  lowerBound?: number;
}

export interface PredictionData {
  symbol: string;
  name: string;
  historicalData: DataPoint[];
  predictions: DataPoint[];
  upperBound?: DataPoint[];
  lowerBound?: DataPoint[];
  predictionType: 'price' | 'volatility' | 'trend';
  timeframe: string;
}

interface PredictionChartProps {
  data: PredictionData;
}

const PredictionChart: React.FC<PredictionChartProps> = ({ data }) => {
  const [timeframe, setTimeframe] = useState<string>(data.timeframe || '30D');
  
  // Combine historical and prediction data for the chart
  const combinedData = [...data.historicalData];
  // Add a visible separation between historical and prediction data
  const lastHistoricalDate = data.historicalData[data.historicalData.length - 1]?.date;
  
  // Process prediction data to match the format needed for the chart
  const chartData: ChartDataPoint[] = [...combinedData];
  
  // Add prediction data points with proper naming
  data.predictions.forEach(point => {
    chartData.push({
      ...point,
      predictedPrice: point.price,
      price: undefined // Now type-safe since price is optional in ChartDataPoint
    });
  });
  
  // Add confidence bounds if available
  if (data.upperBound && data.lowerBound) {
    data.upperBound.forEach((point) => {
      const index = chartData.findIndex(p => p.date === point.date);
      if (index !== -1) {
        chartData[index].upperBound = point.price;
      }
    });
    
    data.lowerBound.forEach((point) => {
      const index = chartData.findIndex(p => p.date === point.date);
      if (index !== -1) {
        chartData[index].lowerBound = point.price;
      }
    });
  }

  // Calculate min/max for chart y-axis with padding
  const allPrices = chartData.flatMap(d => [
    d.price, 
    d.predictedPrice, 
    d.upperBound, 
    d.lowerBound
  ]).filter(Boolean) as number[];

  const dataMin = Math.min(...allPrices);
  const dataMax = Math.max(...allPrices);
  const range = dataMax - dataMin;
  const yMin = dataMin - range * 0.1;
  const yMax = dataMax + range * 0.1;

  // Format for displaying values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  // Generate tooltip content
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      // Check if this is a prediction or historical point
      const isPrediction = payload.some((p: any) => p.name === 'predictedPrice' && p.value !== undefined);
      
      return (
        <div className="prediction-tooltip">
          <p className="date">{label}</p>
          {payload.map((entry: any, index: number) => {
            if (entry.value === undefined) return null;
            
            let label;
            switch(entry.name) {
              case 'price': label = 'Actual Price'; break;
              case 'predictedPrice': label = 'Predicted Price'; break;
              case 'upperBound': label = 'Upper Bound'; break;
              case 'lowerBound': label = 'Lower Bound'; break;
              default: label = entry.name;
            }
            
            return (
              <p key={`item-${index}`} style={{ color: entry.color }}>
                {label}: {formatCurrency(entry.value)}
              </p>
            );
          })}
          {isPrediction && (
            <p className="prediction-note">Forecast</p>
          )}
        </div>
      );
    }
    
    return null;
  };

  // Generate a title for the chart based on prediction type
  const getChartTitle = () => {
    switch(data.predictionType) {
      case 'price': return `Price Forecast for ${data.symbol}`;
      case 'volatility': return `Volatility Prediction for ${data.symbol}`;
      case 'trend': return `Trend Analysis for ${data.symbol}`;
      default: return `Prediction for ${data.symbol}`;
    }
  };

  return (
    <div className="prediction-chart">
      <div className="prediction-header">
        <h2>{getChartTitle()}</h2>
        <div className="prediction-timeframe">
          {['7D', '30D', '90D', '1Y'].map(tf => (
            <button 
              key={tf}
              className={`timeframe-btn ${timeframe === tf ? 'active' : ''}`}
              onClick={() => setTimeframe(tf)}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 12 }}
              tickLine={false}
            />
            <YAxis 
              domain={[yMin, yMax]}
              tick={{ fontSize: 12 }}
              tickFormatter={value => `$${value.toFixed(0)}`}
              tickLine={false}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend 
              iconType="circle" 
              iconSize={10}
              wrapperStyle={{ paddingTop: 10 }}
            />
            
            {/* Historical data */}
            <Area 
              type="monotone" 
              dataKey="price" 
              name="Historical" 
              stroke="#2563eb" 
              fill="url(#colorHistorical)" 
              strokeWidth={2}
              activeDot={{ r: 6 }}
            />
            
            {/* Prediction line */}
            <Area 
              type="monotone" 
              dataKey="predictedPrice" 
              name="Prediction" 
              stroke="#22c55e" 
              fill="url(#colorPrediction)"
              strokeWidth={2}
              strokeDasharray="5 3"
              activeDot={{ r: 6 }}
            />
            
            {/* Confidence interval - only if bounds are provided */}
            {data.upperBound && data.lowerBound && (
              <Area 
                type="monotone" 
                dataKey="upperBound" 
                name="Upper Bound" 
                stroke="transparent" 
                fill="transparent"
                activeDot={false}
              />
            )}
            
            {data.upperBound && data.lowerBound && (
              <Area 
                type="monotone" 
                dataKey="lowerBound" 
                name="Lower Bound" 
                stroke="transparent" 
                fill="url(#colorConfidence)"
                activeDot={false}
              />
            )}
            
            {/* Special marker for transition point from historical to prediction */}
            <ReferenceArea 
              x1={lastHistoricalDate}
              x2={data.predictions[0]?.date} 
              strokeOpacity={0.3}
              stroke="#888"
              fill="#f0f0f0"
              fillOpacity={0.2}
            />
            
            {/* Gradient definitions */}
            <defs>
              <linearGradient id="colorHistorical" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorPrediction" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0.05}/>
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </div>
      
      <div className="prediction-footer">
        <div className="prediction-info">
          <div className="info-item">
            <span className="info-label">Analysis Type:</span>
            <span className="info-value">{data.predictionType.charAt(0).toUpperCase() + data.predictionType.slice(1)} Prediction</span>
          </div>
          <div className="info-item">
            <span className="info-label">Timeframe:</span>
            <span className="info-value">{timeframe} Forecast</span>
          </div>
          <div className="info-item">
            <span className="info-label">Confidence:</span>
            <span className="info-value">{data.upperBound && data.lowerBound ? "95%" : "Not available"}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionChart; 