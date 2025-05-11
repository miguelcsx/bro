import React from 'react';

interface HistoryItem {
  query: string;
  timestamp: string;
}

interface HistoryPanelProps {
  history: HistoryItem[];
  onSelect: (query: string) => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ history, onSelect }) => {
  return (
    <>
      <h3>Bro's keeping your questions</h3>
      <ul>
        {history.map((item, index) => (
          <li key={index} onClick={() => onSelect(item.query)}>
            <span className="query">{item.query}</span>
            <span className="timestamp">{item.timestamp}</span>
          </li>
        ))}
      </ul>
    </>
  );
};

export default HistoryPanel;
