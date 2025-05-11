import React from 'react';
import './StockQuoteDisplay.css';

interface StockQuoteProps {
  data: any;
}

const StockQuoteDisplay: React.FC<StockQuoteProps> = ({ data }) => {
  if (!data) return <div className="stock-loading">Loading stock data...</div>;

  // Extraer los datos relevantes
  const {
    symbol = '',
    name = symbol,
    price = 0,
    change = 0,
    changePercent = 0
  } = data;

  // Extraer datos de estadísticas si están disponibles
  const stats = data.stats || {};
  const {
    open = 'N/A',
    volume = 'N/A',
    dayLow = 'N/A',
    dayHigh = 'N/A',
    yearLow = 'N/A',
    yearHigh = 'N/A'
  } = stats;

  // Format numbers with commas
  const formatNumber = (num: number | string): string => {
    if (num === null || num === undefined || num === 'N/A') return 'N/A';
    if (typeof num === 'number') {
      return num.toLocaleString();
    }
    return num;
  };

  // Format percentage
  const formatPercent = (num: number): string => {
    if (typeof num === 'number') {
      // Ensure the number is a percentage (multiply by 100 if it's in decimal form)
      const percentage = Math.abs(num) < 1 ? num * 100 : num;
      return `${percentage.toFixed(2)}%`;
    }
    return '0.00%';
  };

  return (
    <div className="stock-quote-container">
      <div className="stock-header">
        <h2>{name}</h2>
        <div className="stock-symbol">{symbol}</div>
      </div>
      
      <div className="stock-price-container">
        <div className="stock-price">
          <span className="current-price">
            {typeof price === 'number' ? price.toFixed(2) : price}
          </span>
          <span className="currency">USD</span>
        </div>
        
        <div className={`stock-change ${change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral'}`}>
          <span>{typeof change === 'number' ? change.toFixed(2) : change}</span>
          <span>({formatPercent(changePercent)})</span>
        </div>
      </div>

      <div className="stock-details">
        {open !== 'N/A' && (
          <div className="detail-row">
            <span className="detail-label">Open:</span>
            <span className="detail-value">{formatNumber(open)}</span>
          </div>
        )}
        {(dayLow !== 'N/A' && dayHigh !== 'N/A') && (
          <div className="detail-row">
            <span className="detail-label">Day Range:</span>
            <span className="detail-value">{formatNumber(dayLow)} - {formatNumber(dayHigh)}</span>
          </div>
        )}
        {(yearLow !== 'N/A' && yearHigh !== 'N/A') && (
          <div className="detail-row">
            <span className="detail-label">52 Week Range:</span>
            <span className="detail-value">{formatNumber(yearLow)} - {formatNumber(yearHigh)}</span>
          </div>
        )}
        {volume !== 'N/A' && (
          <div className="detail-row">
            <span className="detail-label">Volume:</span>
            <span className="detail-value">{formatNumber(volume)}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockQuoteDisplay; 