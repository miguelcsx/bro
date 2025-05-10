import React from 'react';

interface StockCardProps {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

const StockCard: React.FC<StockCardProps> = ({
  symbol,
  name,
  price,
  change,
  changePercent
}) => {
  return (
    <div className="stock-card">
      <h3>{name} ({symbol})</h3>
      <div className="price">${price.toFixed(2)}</div>
      <div className={`change ${change >= 0 ? 'positive' : 'negative'}`}>
        {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
      </div>
    </div>
  );
};

export default StockCard;
