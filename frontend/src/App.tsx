import React, { useState } from 'react';
import './App.css';
import StockCard from './components/StockCard';
import PredictionChart, { PredictionData } from './components/PredictionChart';
import { 
  extractPredictionsFromResponse, 
  extractSymbolFromContent,
  containsPredictionQuery,
  createMockPredictionFromText
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

// Date point for predictions and historical data
interface DataPoint {
  date: string;
  price: number;
}

function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // Enhanced stock info parser
  const parseStockInfo = async (content: string): Promise<StockData | null> => {
    // Check if the message matches a pattern like "The current price of X is $Y"
    const stockPattern = /The current price of ([A-Za-z\s]+?)(?:\s*\(([A-Z]+)\))?\s*is\s*\$?([0-9.,]+)/i;
    const match = content.match(stockPattern);
    
    if (match) {
      // Get symbol from message - either direct symbol or attempt to extract it
      const fullName = match[1].trim();
      let symbol = match[2];
      
      if (!symbol) {
        // Try to extract symbol from name if not found
        const symbolMatch = fullName.match(/\(([A-Z]+)\)/);
        symbol = symbolMatch ? symbolMatch[1] : fullName.split(' ')[0].toUpperCase();
      }
      
      const price = parseFloat(match[3].replace(/,/g, ''));
      
      try {
        // In a real-world scenario, fetch actual stock data from your API or a financial API
        // For now, we'll simulate with a mix of real and mock data
        const stockDetails = await fetchStockDetails(symbol);
        
        return {
          symbol: symbol,
          name: fullName,
          price: price,
          change: stockDetails?.change || 0,
          changePercent: stockDetails?.changePercent || 0,
          afterHoursPrice: stockDetails?.afterHoursPrice,
          afterHoursChange: stockDetails?.afterHoursChange,
          afterHoursChangePercent: stockDetails?.afterHoursChangePercent,
          stats: stockDetails?.stats || {
            open: price * 0.99,
            volume: '38.4 M',
            marketCap: '1.88 B',
            dayLow: price * 0.98,
            yearLow: price * 0.8,
            eps: 9.15,
            dayHigh: price * 1.02,
            yearHigh: price * 1.3,
            peRatio: 16.91
          }
        };
      } catch (error) {
        console.error('Error fetching stock details:', error);
        
        // Fallback with basic data if API fails
        return {
          symbol: symbol,
          name: fullName,
          price: price,
          change: price * 0.02, // Mock 2% change
          changePercent: 2,
          stats: {
            open: price * 0.99,
            volume: '38.4 M',
            marketCap: '1.88 B',
            dayLow: price * 0.98,
            yearLow: price * 0.8,
            eps: 9.15,
            dayHigh: price * 1.02,
            yearHigh: price * 1.3,
            peRatio: 16.91
          }
        };
      }
    }
    
    return null;
  };

  // Check if response contains prediction data
  const parsePredictionData = (content: string, apiResponse: any): PredictionData | null => {
    // Skip if the content doesn't appear to be prediction-related
    if (!containsPredictionQuery(content)) {
      return null;
    }
    
    // Extract symbol from the content
    const symbol = extractSymbolFromContent(content);
    if (!symbol) {
      return null;
    }
    
    // First try to use the helper function to extract prediction data from the API response
    const extractedData = extractPredictionsFromResponse(apiResponse, symbol);
    
    // If we found structured data, return it
    if (extractedData) {
      return extractedData;
    }
    
    // Otherwise, try to generate mock data from the text content
    // This helps when the backend returns text predictions without structured data
    console.log('No structured data found, trying to create mock data from text');
    return createMockPredictionFromText(content);
  };

  // Mock function to fetch stock details - in a real app, connect to your API or financial data provider
  const fetchStockDetails = async (symbol: string): Promise<Partial<StockData> | null> => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // This is where you would fetch real data from your server or financial API
    // return fetch(`/api/stock/${symbol}`).then(res => res.json());
    
    // For demo, return mock data with some randomization
    const basePrice = Math.random() * 100 + 50; // Random price between 50-150
    const change = (Math.random() * 6) - 3; // Random change -3 to +3
    const changePercent = (change / basePrice) * 100;
    
    return {
      change,
      changePercent,
      afterHoursPrice: basePrice + (Math.random() * 2 - 1),
      afterHoursChange: Math.random() * 2 - 1,
      afterHoursChangePercent: Math.random() * 2 - 1,
      stats: {
        open: basePrice - Math.random() * 2,
        volume: `${Math.floor(Math.random() * 100)} M`,
        marketCap: `${Math.floor(Math.random() * 100) / 10} B`,
        dayLow: basePrice - Math.random() * 5,
        yearLow: basePrice - Math.random() * 20,
        eps: Math.random() * 10,
        dayHigh: basePrice + Math.random() * 5,
        yearHigh: basePrice + Math.random() * 20,
        peRatio: Math.random() * 30 + 10
      }
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    // Add user message to chat
    setMessages(prev => [...prev, {role: 'user', content: query}]);
    setQuery('');
    setLoading(true);

    try {
      // Call the API
      const response = await fetch('http://localhost:8888/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      const data = await response.json();
      console.log('Raw API response:', data);
      
      if (data.success && data.content) {
        // Check for predictions directly in the response
        let predictionData: PredictionData | null = null;
        let aiMessage: string | null = null;
        
        // If the API returns prediction data directly in a dedicated field
        if (data.predictions) {
          console.log('Found predictions in data:', data.predictions);
          predictionData = data.predictions;
          aiMessage = data.ai_response || 'Here\'s the forecast you requested.';
        } else {
          // Extract the last AIMessage with non-empty content
          const content = data.content;
          console.log('No predictions field, looking in content:', content);
          
          // Use regex to find the last AIMessage with content
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
            console.log('Extracted aiMessage:', aiMessage);
            
            // Check if the content contains prediction query patterns
            console.log('Checking if content contains prediction patterns:', containsPredictionQuery(lastMatch));
            console.log('Extracted symbol:', extractSymbolFromContent(lastMatch));
            
            // Check for predictions in the response
            predictionData = parsePredictionData(lastMatch as string, data);
            console.log('Parsed prediction data:', predictionData);
          } else {
            // Try alternative regex if the first one failed
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
        
        // Now we have either a predictionData object or null
        if (aiMessage) {
          try {
            // If we already have prediction data, use it
            if (predictionData) {
              // Use a type assertion to tell TypeScript this is a Message object
              const messageObj: Message = {
                role: 'assistant', 
                content: aiMessage || 'Here\'s the forecast you requested.',
                predictionData // TypeScript knows this is non-null inside this if block
              };
              setMessages(prev => [...prev, messageObj]);
            } else {
              // Otherwise try to extract stock data
              const stockData = await parseStockInfo(aiMessage || '');
              
              if (stockData) {
                // If stock data found, add it to the message
                const messageObj: Message = {
                  role: 'assistant', 
                  content: aiMessage || 'Here\'s the stock information you requested.',
                  stockData
                };
                setMessages(prev => [...prev, messageObj]);
              } else {
                // Regular text response - no predictionData or stockData here
                const messageObj: Message = {
                  role: 'assistant', 
                  content: aiMessage || 'Sorry, I couldn\'t process that request properly.'
                };
                setMessages(prev => [...prev, messageObj]);
              }
            }
          } catch (error) {
            console.error("Error handling response:", error);
            const messageObj: Message = {
              role: 'assistant', 
              content: aiMessage || 'Sorry, something went wrong. Please try again.'
            };
            setMessages(prev => [...prev, messageObj]);
          }
        } else {
          const messageObj: Message = {
            role: 'assistant', 
            content: 'Sorry, I couldn\'t process that request properly.'
          };
          setMessages(prev => [...prev, messageObj]);
        }
      } else {
        const messageObj: Message = {
          role: 'assistant', 
          content: 'Sorry, I had trouble processing that request.'
        };
        setMessages(prev => [...prev, messageObj]);
      }
    } catch (error) {
      console.error('Error fetching response:', error);
      const messageObj: Message = {
        role: 'assistant', 
        content: 'Sorry, something went wrong. Please try again.'
      };
      setMessages(prev => [...prev, messageObj]);
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
                {msg.role === 'assistant' && msg.predictionData ? (
                  <PredictionChart data={msg.predictionData} />
                ) : msg.role === 'assistant' && msg.stockData ? (
                  <StockCard {...msg.stockData} />
                ) : (
                  msg.content
                )}
              </div>
            ))}
            {loading && <div className="message assistant">Bro is thinking...</div>}
          </div>
        ) : (
          // Empty state - just leave it empty
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
