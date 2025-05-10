import React, { useState } from 'react';
import './App.css';
import StockCard from './components/StockCard';
import PredictionChart, { PredictionData } from './components/PredictionChart';
import { 
  extractPredictionsFromResponse, 
  extractSymbolFromContent,
  containsPredictionQuery
} from './utils/predictionHelpers';

// Define types for message content
interface Message {
  role: string;
  content: string;
  stockData?: StockData;
  predictionData?: PredictionData;
}

// Stock data interface
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

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // Only extract stock info if it looks like real data
  const parseStockInfo = async (content: string): Promise<StockData | null> => {
    // Example: parse only if the content matches a real data pattern
    const stockPattern = /The current price of ([A-Za-z\s]+?)(?:\s*\(([A-Z]+)\))?\s*is\s*\$?([0-9.,]+)/i;
    const match = content.match(stockPattern);
    if (match) {
      // Only use if you have a real API to fetch details
      // Otherwise, return null to avoid mock data
      return null;
    }
    return null;
  };

  // Only use prediction data if present in the API response
  const parsePredictionData = (content: string, apiResponse: any): PredictionData | null => {
    if (!containsPredictionQuery(content)) {
      return null;
    }
    const symbol = extractSymbolFromContent(content);
    if (!symbol) {
      return null;
    }
    const extractedData = extractPredictionsFromResponse(apiResponse, symbol);
    if (extractedData) {
      return extractedData;
    }
    // Do NOT generate mock data here
    return null;
  };

  // Remove the mock fetchStockDetails function entirely

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setMessages(prev => [...prev, {role: 'user', content: query}]);
    setQuery('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8888/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      let aiMessage: string | null = null;
      let predictionData: PredictionData | null = null;

      if (data.success && data.content) {
        if (data.predictions) {
          predictionData = data.predictions;
          aiMessage = data.ai_response || 'Here\'s the forecast you requested.';
        } else {
          const content = data.content;
          const regex = /AIMessage\(content='([^']+)'[^)]*\)/g;
          let match;
          let lastMatch: string | null = null;
          while ((match = regex.exec(content)) !== null) {
            if (match[1] && match[1].trim() !== '') {
              lastMatch = match[1];
            }
          }
          if (lastMatch) {
            aiMessage = lastMatch;
            predictionData = parsePredictionData(lastMatch, data);
          } else {
            const altRegex = /content='([^']+)'[^,]*id='run--/;
            const altMatch = content.match(altRegex);
            if (altMatch && altMatch[1]) {
              aiMessage = altMatch[1];
              predictionData = parsePredictionData(altMatch[1], data);
            } else {
              aiMessage = 'I found information but couldn\'t format it properly.';
            }
          }
        }

        if (aiMessage) {
          try {
            if (predictionData) {
              // Only show chart if real prediction data exists
              setMessages(prev => [
                ...prev,
                { role: 'assistant', content: aiMessage || '', ...(predictionData ? { predictionData } : {}) }
              ]);
            } else {
              // Try to extract real stock data (but do not generate mock)
              const stockData = await parseStockInfo(aiMessage || '');
              if (stockData) {
                setMessages(prev => [
                  ...prev,
                  { role: 'assistant', content: aiMessage || '', ...(stockData ? { stockData } : {}) }
                ]);
              } else {
                setMessages(prev => [
                  ...prev,
                  { role: 'assistant', content: aiMessage || '' }
                ]);
              }
            }
          } catch (error) {
            setMessages(prev => [
              ...prev,
              { role: 'assistant', content: aiMessage || 'Sorry, something went wrong. Please try again.' }
            ]);
          }
        } else {
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: 'Sorry, I couldn\'t process that request properly.' }
          ]);
        }
      } else {
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: 'Sorry, I had trouble processing that request.' }
        ]);
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
    <div className="app">
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
                {/* Only render charts/cards if real data exists */}
                {msg.role === 'assistant' && msg.predictionData ? (
                  // <PredictionChart data={msg.predictionData} />
                  msg.content
                ) : msg.role === 'assistant' && msg.stockData ? (
                  // <StockCard {...msg.stockData} />
                  msg.content
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
  );
}

export default App;
