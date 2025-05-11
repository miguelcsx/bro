import React, { useState, useEffect } from 'react';
import './App.css';

// Component imports
import HistoryPanel from './components/HistoryPanel';
import PredictionChart from './components/PredictionChart';
import PredictionTable from './components/PredictionTable';
import StockQuoteDisplay from './components/StockQuoteDisplay';
import Dashboard from './components/Dashboard';
import HistoricalChart from './components/HistoricalChart';

// Define types
interface Message {
  role: string;
  content: string;
  stockData?: StockData;
  predictionData?: PredictionData;
  dashboardData?: DashboardData;
}

// Stock data types
interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  currency?: string;
  marketState?: string;
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
    previousClose?: number;
  };
  company?: {
    sector?: string;
    industry?: string;
    country?: string;
    employees?: number;
    website?: string;
    summary?: string;
  };
}

// New interface for the backend API response
interface ApiResponse {
  success: boolean;
  message: string;
  data: StockQuoteData | null;
  dashboard?: DashboardData;
}

// Chart data types
interface ChartData {
  id: string;
  title: string;
  type: string;
  data: any[];
  x_axis: string;
  y_axis: string;
  currency: string;
}

// News article type
interface NewsArticle {
  title: string;
  source: string;
  date: string;
  summary: string;
  url: string;
}

// Market overview type
interface MarketOverview {
  market_status: string;
  trending_stocks: {
    symbol: string;
    name: string;
    change: number;
  }[];
  market_indexes: {
    name: string;
    value: number;
    change: number;
  }[];
}

// Dashboard data type
interface DashboardData {
  stock_info: StockData | null;
  charts: ChartData[];
  news: NewsArticle[];
  market_overview: MarketOverview;
}

// Type for the stock quote data from backend
interface StockQuoteData {
  type: string;
  symbol: string;
  name: string;
  price: number;
  currency: string;
  change: number;
  changePercent: number;
  marketState: string;
  details: {
    previousClose: number;
    open: number;
    dayLow: number;
    dayHigh: number;
    volume: number;
    averageVolume: number;
    fiftyTwoWeekLow: number;
    fiftyTwoWeekHigh: number;
  };
  company: {
    sector: string;
    industry: string;
    country: string;
    employees: number;
    website: string;
    summary: string;
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentDashboard, setCurrentDashboard] = useState<DashboardData | null>(null);
  const [activeChart, setActiveChart] = useState('historical');
  const [isStockDetailsCollapsed, setIsStockDetailsCollapsed] = useState(true);

  // Optional: Load an example on startup for demonstration
  useEffect(() => {
    // handleExampleQuery();
  }, []);

  const handleExampleQuery = async () => {
    const exampleQuery = "cuanto vale Google?";
    setQuery(exampleQuery);
    await handleSubmit(new Event('submit') as any);
  };

  const parseStockInfo = async (content: string): Promise<StockData | null> => {
    return null;
  };

  const parsePredictionData = (content: string, apiResponse: any): PredictionData | null => {
    if (apiResponse.data?.raw_forecast) {
      return apiResponse.data.raw_forecast;
    }
    return null;
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
      
      // Create dashboard data structure
      const dashboardData: DashboardData = {
        stock_info: null,
        charts: [],
        news: [],
        market_overview: {
          market_status: "",
          trending_stocks: [],
          market_indexes: []
        }
      };
      
      let newMessage: Message = { 
        role: 'assistant', 
        content: data.message || "No se pudo procesar la solicitud."
      };
      
      // Process stock data
      if (data.symbol) {
        // Create stock info object
        const stockInfo: StockData = {
          symbol: data.symbol,
          name: data.name,
          price: data.price,
          change: data.change,
          changePercent: data.changePercent,
          currency: data.currency,
          marketState: data.marketState,
          stats: {
            open: data.details?.open,
            volume: String(data.details?.volume || 0),
            dayLow: data.details?.dayLow,
            dayHigh: data.details?.dayHigh,
            yearLow: data.details?.fiftyTwoWeekLow,
            yearHigh: data.details?.fiftyTwoWeekHigh,
            previousClose: data.details?.previousClose
          },
          company: data.company
        };
        
        newMessage.stockData = stockInfo;
        dashboardData.stock_info = stockInfo;
        
        // Create historical chart if we have historical data
        if (data.historical_data && data.historical_data.length > 0) {
          dashboardData.charts.push({
            id: 'historical_price',
            title: 'Historical Price',
            type: 'line',
            data: data.historical_data,
            x_axis: 'Date',
            y_axis: 'Price',
            currency: data.currency || 'USD'
          });
        }
        
        // Create prediction chart if we have prediction data
        if (data.predictions && data.predictions.length > 0) {
          dashboardData.charts.push({
            id: 'price_prediction',
            title: 'Price Prediction',
            type: 'line',
            data: data.predictions,
            x_axis: 'Date',
            y_axis: 'Price',
            currency: data.currency || 'USD'
          });
          
          newMessage.predictionData = data.predictions.reduce((acc: PredictionData, pred: any) => {
            acc[pred.date] = {
              Predicted: pred.predicted,
              Lower: pred.lower,
              Upper: pred.upper
            };
            return acc;
          }, {} as PredictionData);
        }
        
        // Add news data
        if (data.news && data.news.length > 0) {
          dashboardData.news = data.news;
        }
        
        // Set dashboard data on the message and update state
        newMessage.dashboardData = dashboardData;
        setCurrentDashboard(dashboardData);
      }
      
      setMessages(prev => [...prev, newMessage]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Lo siento, algo salió mal. Por favor intenta de nuevo.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Render dashboard with existing style classes
  return (
    <div className="dashboard-layout">
      {/* Sidebar para historial */}
      <div className={`history-sidebar ${sidebarOpen ? '' : 'closed'}`}>
        <button 
          className="toggle-sidebar-btn" 
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? '◀' : '▶'}
        </button>
        
        <div className="history-content">
          <h3>Chat History</h3>
          <div className="history-list">
            {history.map((item, index) => (
              <div key={index} className="history-item">
                {item.query}
                <small>{item.timestamp}</small>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Contenido principal */}
      <div className="dashboard-main">
        {/* Header fijo */}
        <div className="dashboard-title">
          <div className="logo-container">
            <img src="/logo.jpeg" alt="Bro Logo" className="logo-image" />
            <div className="logo-text">
              <h1>Hey, I'm Bro</h1>
              <p>What stocks would you like to see today?</p>
            </div>
          </div>
        </div>
        
        {/* Panel de información de acción, solo mostrar si hay datos */}
        {currentDashboard?.stock_info && (
          <div className="stock-info-panel">
            <div className="stock-header">
              <div className="stock-title">
                <h2>{currentDashboard.stock_info.name} ({currentDashboard.stock_info.symbol})</h2>
                <div className="market-status">
                  {currentDashboard.stock_info.marketState || 'Market Closed'}
                </div>
              </div>
              <div className="stock-price-info">
                <div className="stock-price">
                  {currentDashboard.stock_info.currency || '$'}{currentDashboard.stock_info.price.toFixed(2)}
                </div>
                <div className={`stock-change ${currentDashboard.stock_info.change >= 0 ? 'positive' : 'negative'}`}>
                  {currentDashboard.stock_info.change >= 0 ? '+' : ''}{currentDashboard.stock_info.change.toFixed(2)} 
                  ({currentDashboard.stock_info.changePercent.toFixed(2)}%)
                </div>
                <button 
                  onClick={() => setIsStockDetailsCollapsed(!isStockDetailsCollapsed)}
                  className="toggle-details-btn"
                  aria-label={isStockDetailsCollapsed ? 'Show Details' : 'Hide Details'}
                >
                  {isStockDetailsCollapsed ? (
                    <span style={{fontSize: '1.5rem', lineHeight: 1}}>&#x25BC;</span> // Down arrow
                  ) : (
                    <span style={{fontSize: '1.5rem', lineHeight: 1}}>&#x25B2;</span> // Up arrow
                  )}
                </button>
              </div>
            </div>
            
            {!isStockDetailsCollapsed && (
              <div className="stock-details">
                <div className="stock-stats">
                  {currentDashboard.stock_info.stats?.open !== undefined && (
                    <div className="stat-row">
                      <span className="stat-label">Open</span>
                      <span className="stat-value">{currentDashboard.stock_info.currency || '$'}{currentDashboard.stock_info.stats.open.toFixed(2)}</span>
                    </div>
                  )}
                  {currentDashboard.stock_info.stats?.previousClose !== undefined && (
                    <div className="stat-row">
                      <span className="stat-label">Previous Close</span>
                      <span className="stat-value">{currentDashboard.stock_info.currency || '$'}{currentDashboard.stock_info.stats.previousClose.toFixed(2)}</span>
                    </div>
                  )}
                  {currentDashboard.stock_info.stats?.dayLow !== undefined && (
                    <div className="stat-row">
                      <span className="stat-label">Day Low</span>
                      <span className="stat-value">{currentDashboard.stock_info.currency || '$'}{currentDashboard.stock_info.stats.dayLow.toFixed(2)}</span>
                    </div>
                  )}
                  {currentDashboard.stock_info.stats?.dayHigh !== undefined && (
                    <div className="stat-row">
                      <span className="stat-label">Day High</span>
                      <span className="stat-value">{currentDashboard.stock_info.currency || '$'}{currentDashboard.stock_info.stats.dayHigh.toFixed(2)}</span>
                    </div>
                  )}
                  {currentDashboard.stock_info.stats?.volume && (
                    <div className="stat-row">
                      <span className="stat-label">Volume</span>
                      <span className="stat-value">{currentDashboard.stock_info.stats.volume}</span>
                    </div>
                  )}
                </div>
                
                {currentDashboard.stock_info.company?.website && (
                  <div className="company-link">
                    <a href={currentDashboard.stock_info.company.website} target="_blank" rel="noopener noreferrer">
                      Visit Website
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        {/* Contenedor de contenido principal */}
        <div className="content-container">
          {/* Columna izquierda - Gráficos */}
          <div className="left-column">
            {currentDashboard ? (
              <>
                <div className="charts-panel">
                  <div className="chart-tabs">
                    <button 
                      className={`chart-tab ${activeChart === 'historical' ? 'active' : ''}`}
                      onClick={() => setActiveChart('historical')}
                    >
                      Historical Price
                    </button>
                    <button 
                      className={`chart-tab ${activeChart === 'prediction' ? 'active' : ''}`}
                      onClick={() => setActiveChart('prediction')}
                    >
                      Price Prediction
                    </button>
                  </div>
                  
                  <div className="chart-display">
                    {currentDashboard.charts && currentDashboard.charts.length > 0 ? (
                      <div className="chart-container">
                        {/* Display the appropriate chart based on selected tab */}
                        {activeChart === 'historical' ? (
                          <HistoricalChart 
                            data={currentDashboard.charts.find(chart => chart.id === 'historical_price')?.data || []} 
                            currency={currentDashboard.charts.find(chart => chart.id === 'historical_price')?.currency || '$'}
                          />
                        ) : (
                          <PredictionChart 
                            data={currentDashboard.charts.find(chart => chart.id === 'price_prediction')?.data || []} 
                            currency={currentDashboard.charts.find(chart => chart.id === 'price_prediction')?.currency || '$'}
                          />
                        )}
                      </div>
                    ) : (
                      <div className="no-data">No chart data available</div>
                    )}
                  </div>
                </div>
                
                {currentDashboard.stock_info?.company && (
                  <div className="company-info">
                    <h3>Company Information</h3>
                    <div className="company-details">
                      <div className="company-meta">
                        {currentDashboard.stock_info.company.sector && (
                          <div className="meta-item">
                            <span className="meta-label">Sector</span>
                            <span className="meta-value">{currentDashboard.stock_info.company.sector}</span>
                          </div>
                        )}
                        {currentDashboard.stock_info.company.industry && (
                          <div className="meta-item">
                            <span className="meta-label">Industry</span>
                            <span className="meta-value">{currentDashboard.stock_info.company.industry}</span>
                          </div>
                        )}
                        {currentDashboard.stock_info.company.country && (
                          <div className="meta-item">
                            <span className="meta-label">Country</span>
                            <span className="meta-value">{currentDashboard.stock_info.company.country}</span>
                          </div>
                        )}
                        {currentDashboard.stock_info.company.employees && (
                          <div className="meta-item">
                            <span className="meta-label">Employees</span>
                            <span className="meta-value">{currentDashboard.stock_info.company.employees.toLocaleString()}</span>
                          </div>
                        )}
                      </div>
                      
                      {currentDashboard.stock_info.company.summary && (
                        <div className="company-summary">
                          {currentDashboard.stock_info.company.summary}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="empty-state">
                <div className="logo-container">
                  <img src="/logo.jpeg" alt="Bro Logo" className="logo-image" />
                  <div className="logo-text">
                    <h1>Hey, I'm Bro</h1>
                    <p>What stocks would you like to see today?</p>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          {/* Columna derecha - Historial de chat */}
          <div className="right-column">
            <div className="chat-history-panel">
              <h3>Chat with Bro</h3>
              
              <div className="chat-messages-history">
                {messages.map((msg, i) => (
                  <div key={i} className={`chat-message ${msg.role}`}>
                    <div className="message-content">{msg.content}</div>
                  </div>
                ))}
                {loading && <div className="chat-loading">Bro is thinking...</div>}
              </div>
            </div>
          </div>
          
          {/* Sidebar de noticias */}
          {currentDashboard?.news && currentDashboard.news.length > 0 && (
            <div className="news-sidebar">
              <div className="news-panel">
                <h3>Latest News</h3>
                <div className="news-list">
                  {currentDashboard.news.map((item, index) => (
                    <div key={index} className="news-item">
                      <h4 className="news-title">{item.title}</h4>
                      <div className="news-meta">
                        <span>{item.source}</span>
                        <span>{item.date}</span>
                      </div>
                      <p className="news-summary">{item.summary}</p>
                      <a href={item.url} className="news-link" target="_blank" rel="noopener noreferrer">Read more</a>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Área de chat inferior */}
        <div className="chat-input-area">
          <form onSubmit={handleSubmit} className="chat-form">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask me about any stock"
              className="chat-input"
            />
            <button type="submit" className="chat-submit">→</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
