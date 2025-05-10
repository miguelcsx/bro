import React, { useState } from 'react';
import './App.css';

// Component imports
import HistoryPanel from './components/HistoryPanel';
import PredictionChart from './components/PredictionChart';
import PredictionTable from './components/PredictionTable';
import StockCard from './components/StockCard';

// Define types
interface Message {
  role: string;
  content: string;
  stockData?: StockData;
  predictionData?: PredictionData;
}

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  afterHoursPrice?: number;
  afterHoursChange?: number;
  afterHoursChangePercent?: number;
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

interface HistoryItem {
  query: string;
  timestamp: string;
}

interface PredictionData {
  [date: string]: {
    Predicted: number;
    Lower: number;
    Upper: number;
  };
}

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  const parseStockInfo = async (content: string): Promise<StockData | null> => {
    return null;
  };

  const parsePredictionData = (content: string, apiResponse: any): PredictionData | null => {
    // First check if the API response contains structured data
    if (apiResponse.metadata?.raw_forecast) {
      return apiResponse.metadata.raw_forecast;
    }

    // Fallback to text parsing if structured data isn't available
    const predictionPattern = /(\d{4}-\d{2}-\d{2}): \$([\d.]+) \(\$([\d.]+)-\$([\d.]+)\)/g;
    const predictions: PredictionData = {};
    
    let match;
    while ((match = predictionPattern.exec(content)) !== null) {
      const [_, date, predicted, lower, upper] = match;
      predictions[date] = {
        Predicted: parseFloat(predicted),
        Lower: parseFloat(lower),
        Upper: parseFloat(upper)
      };
    }

    return Object.keys(predictions).length > 0 ? predictions : null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setHistory(prev => [
      { query, timestamp: new Date().toLocaleString() },
      ...prev
    ]);

    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setQuery('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8888/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      let aiMessage: string = ''; // Always string, never null
      let predictionData: PredictionData | null = null;

      if (data.success) {
        // Ensure aiMessage is always a string
        aiMessage = data.text || data.content || 'Here\'s the forecast you requested.';
        
        // Get prediction data
        predictionData = data.metadata?.raw_forecast || parsePredictionData(aiMessage, data);

        // Get stock data
        const stockData = await parseStockInfo(aiMessage);
        
        setMessages(prev => [
          ...prev,
          { 
            role: 'assistant', 
            content: aiMessage, // Now guaranteed to be string
            ...(predictionData ? { predictionData } : {}),
            ...(stockData ? { stockData } : {})
          }
        ]);
      } else {
        aiMessage = 'Sorry, I had trouble processing that request.';
        setMessages(prev => [...prev, { role: 'assistant', content: aiMessage }]);
      }
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <HistoryPanel 
        history={history}
        onSelect={(selectedQuery) => setQuery(selectedQuery)}
      />
      
      <div className="main-content">
        <div className="header">
          <div className="logo-container">
            <div className="logo-icon">💸</div>
            <div className="logo-text">
              <h1>Hey, I'm Bro</h1>
              <p>What stocks would you like to see today?</p>
            </div>
          </div>
        </div>

        <div className="chat-container">
          {messages.length > 0 ? (
            <div className="messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  {msg.role === 'assistant' && msg.predictionData ? (
                    <div className="response-container">
                      <p>{msg.content}</p>
                      <PredictionTable data={msg.predictionData} />
                      <PredictionChart data={msg.predictionData} />
                    </div>
                  ) : msg.role === 'assistant' && msg.stockData ? (
                    <div className="response-container">
                      <p>{msg.content}</p>
                      <StockCard {...msg.stockData} />
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
              ))}
              {loading && <div className="message assistant">Bro is thinking...</div>}
            </div>
          ) : (
            <div className="messages-empty"></div>
          )}

          <form onSubmit={handleSubmit} className="input-container">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Message Bro"
            />
            <button type="submit">→</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
