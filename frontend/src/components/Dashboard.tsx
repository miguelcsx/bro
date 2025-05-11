import React, { useState } from 'react';
import './Dashboard.css';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

// Registrar los componentes de ChartJS
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Tipos
interface DashboardProps {
  data: any;
  messages: any[];
  loading: boolean;
  query: string;
  onQueryChange: (query: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

interface ChartData {
  id: string;
  title: string;
  type: string;
  data: any[];
  x_axis: string;
  y_axis: string;
  currency: string;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  data, 
  messages, 
  loading, 
  query, 
  onQueryChange, 
  onSubmit 
}) => {
  const [historySidebarOpen, setHistorySidebarOpen] = useState(false);
  const [activeChartIndex, setActiveChartIndex] = useState(0);

  // Formato de números
  const formatNumber = (num: number | null) => {
    if (num === null || isNaN(num)) return 'N/A';
    return num.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };

  // Formato de cambio porcentual
  const formatPercentChange = (change: number | null) => {
    if (change === null || isNaN(change)) return 'N/A';
    return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
  };

  // Crear datos del gráfico histórico
  const createHistoricalChart = (chartData: ChartData) => {
    if (!chartData || !chartData.data || chartData.data.length === 0) {
      return null;
    }

    const labels = chartData.data.map(item => item.date);
    const prices = chartData.data.map(item => item.price);

    const data = {
      labels,
      datasets: [
        {
          label: 'Price',
          data: prices,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
          tension: 0.3,
        }
      ]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: chartData.title,
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              return `${context.dataset.label}: ${chartData.currency} ${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          grid: {
            color: 'rgba(200, 200, 200, 0.2)'
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index' as const,
      }
    };

    return (
      <div className="chart-container">
        <Line data={data} options={options} />
      </div>
    );
  };

  // Crear datos del gráfico de predicción
  const createPredictionChart = (chartData: ChartData) => {
    if (!chartData || !chartData.data || chartData.data.length === 0) {
      return null;
    }

    const labels = chartData.data.map(item => item.date);
    const predicted = chartData.data.map(item => item.predicted);
    const upper = chartData.data.map(item => item.upper);
    const lower = chartData.data.map(item => item.lower);

    const data = {
      labels,
      datasets: [
        {
          label: 'Predicted',
          data: predicted,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
          tension: 0.3,
        },
        {
          label: 'Upper Bound',
          data: upper,
          borderColor: 'rgba(255, 99, 132, 0.2)',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          pointRadius: 0,
          tension: 0.3,
        },
        {
          label: 'Lower Bound',
          data: lower,
          borderColor: 'rgba(255, 99, 132, 0.2)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: '+1',
          tension: 0.3,
        }
      ]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: chartData.title,
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              return `${context.dataset.label}: ${chartData.currency} ${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          grid: {
            color: 'rgba(200, 200, 200, 0.2)'
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index' as const,
      }
    };

    return (
      <div className="chart-container">
        <Line data={data} options={options} />
      </div>
    );
  };

  // Encontrar los gráficos disponibles
  const availableCharts = data.charts || [];

  // Filtrar solo los mensajes relevantes para el historial del chat
  const relevantMessages = messages.filter(msg => 
    msg.role === 'user' || (msg.role === 'assistant' && !msg.stockData)
  );

  return (
    <div className="dashboard-layout">
      {/* Sidebar para historial de chats */}
      <div className={`history-sidebar ${historySidebarOpen ? 'open' : 'closed'}`}>
        <div className="history-content">
          <h2>Historial de Chats</h2>
          <div className="history-list">
            {messages.map((msg, i) => (
              msg.role === 'user' && (
                <div key={i} className="history-item">
                  {msg.content}
                </div>
              )
            ))}
          </div>
        </div>
        <button 
          className="toggle-sidebar-btn"
          onClick={() => setHistorySidebarOpen(!historySidebarOpen)}
        >
          {historySidebarOpen ? '←' : '→'}
        </button>
      </div>
      
      {/* Contenido principal */}
      <div className="dashboard-main">
        {/* Título fijo */}
        <div className="dashboard-title">
          <h1>Bro</h1>
        </div>

        {/* Header con la información de la acción */}
        {data.stock_info && (
          <div className="stock-info-panel">
            <div className="stock-header">
              <div className="stock-title">
                <h2>{data.stock_info.name} ({data.stock_info.symbol})</h2>
                <div className="market-status">
                  {data.stock_info.marketState === 'REGULAR' ? 'Mercado Abierto' : 'Mercado Cerrado'}
                </div>
              </div>
              <div className="stock-price-info">
                <div className="stock-price">{data.stock_info.currency} {formatNumber(data.stock_info.price)}</div>
                <div className={`stock-change ${data.stock_info.change >= 0 ? 'positive' : 'negative'}`}>
                  {data.stock_info.change >= 0 ? '+' : ''}{formatNumber(data.stock_info.change)} 
                  ({formatPercentChange(data.stock_info.changePercent)})
                </div>
              </div>
            </div>
            
            <div className="stock-details">
              {data.stock_info.stats && (
                <div className="stock-stats">
                  <div className="stat-row">
                    <span className="stat-label">Apertura</span>
                    <span className="stat-value">{formatNumber(data.stock_info.stats.open)}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Cierre Previo</span>
                    <span className="stat-value">{formatNumber(data.stock_info.stats.previousClose)}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Rango del Día</span>
                    <span className="stat-value">
                      {formatNumber(data.stock_info.stats.dayLow)} - {formatNumber(data.stock_info.stats.dayHigh)}
                    </span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Rango 52 Semanas</span>
                    <span className="stat-value">
                      {formatNumber(data.stock_info.stats.yearLow)} - {formatNumber(data.stock_info.stats.yearHigh)}
                    </span>
                  </div>
                </div>
              )}
              
              {data.stock_info.company && data.stock_info.company.website && (
                <div className="company-link">
                  <a href={data.stock_info.company.website} target="_blank" rel="noopener noreferrer">
                    Sitio Web Oficial
                  </a>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Contenedor principal de 2 columnas + sidebar derecha */}
        <div className="content-container">
          {/* Columna izquierda: Gráficos interactivos */}
          <div className="left-column">
            <div className="charts-panel">
              <div className="chart-tabs">
                {availableCharts.map((chart: ChartData, index: number) => (
                  <button 
                    key={chart.id}
                    className={`chart-tab ${index === activeChartIndex ? 'active' : ''}`}
                    onClick={() => setActiveChartIndex(index)}
                  >
                    {chart.title.includes('Historical') ? 'Histórico' : 
                     chart.title.includes('Prediction') ? 'Predicción' : chart.title}
                  </button>
                ))}
              </div>
              
              <div className="chart-display">
                {availableCharts.length > 0 ? (
                  activeChartIndex === 0 ? 
                    createHistoricalChart(availableCharts[0]) : 
                    createPredictionChart(availableCharts[1])
                ) : (
                  <div className="no-data">No hay datos de gráficos disponibles</div>
                )}
              </div>
            </div>
            
            {data.stock_info && data.stock_info.company && (
              <div className="company-info">
                <h3>Acerca de {data.stock_info.name}</h3>
                <div className="company-details">
                  <div className="company-meta">
                    <div className="meta-item">
                      <span className="meta-label">Sector</span>
                      <span className="meta-value">{data.stock_info.company.sector || 'N/A'}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Industria</span>
                      <span className="meta-value">{data.stock_info.company.industry || 'N/A'}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Empleados</span>
                      <span className="meta-value">{formatNumber(data.stock_info.company.employees) || 'N/A'}</span>
                    </div>
                  </div>
                  
                  {data.stock_info.company.summary && (
                    <div className="company-summary">
                      {data.stock_info.company.summary}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          
          {/* Columna derecha: Historial de chat */}
          <div className="right-column">
            <div className="chat-history-panel">
              <h3>Historial de Conversación</h3>
              <div className="chat-messages-history">
                {relevantMessages.map((msg, i) => (
                  <div key={i} className={`chat-message ${msg.role}`}>
                    <div className="message-content">{msg.content}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {/* Barra lateral derecha: Noticias */}
          <div className="news-sidebar">
            <div className="news-panel">
              <h3>Noticias Recientes</h3>
              <div className="news-list">
                {data.news && data.news.map((article: any, i: number) => (
                  <div key={i} className="news-item">
                    <h4 className="news-title">{article.title}</h4>
                    <div className="news-meta">
                      <span className="news-source">{article.source}</span>
                      <span className="news-date">{article.date}</span>
                    </div>
                    <p className="news-summary">{article.summary}</p>
                    <a href={article.url} className="news-link" target="_blank" rel="noopener noreferrer">
                      Leer más
                    </a>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        
        {/* Área de chat en la parte inferior */}
        <div className="chat-input-area">
          <form onSubmit={onSubmit} className="chat-form">
            <input
              type="text"
              value={query}
              onChange={(e) => onQueryChange(e.target.value)}
              placeholder="Pregunta algo sobre esta acción..."
              className="chat-input"
            />
            <button type="submit" className="chat-submit">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M15.964.686a.5.5 0 0 0-.65-.65L.767 5.855H.766l-.452.18a.5.5 0 0 0-.082.887l.41.26.001.002 4.995 3.178 3.178 4.995.002.002.26.41a.5.5 0 0 0 .886-.083l6-15Zm-1.833 1.89L6.637 10.07l-.215-.338a.5.5 0 0 0-.154-.154l-.338-.215 7.494-7.494 1.178-.471-.47 1.178Z"/>
              </svg>
            </button>
          </form>
          {loading && <div className="chat-loading">Bro está pensando...</div>}
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 