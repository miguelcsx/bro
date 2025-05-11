import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
  } from 'chart.js';
  import React from 'react';
  import { Line } from 'react-chartjs-2';
  

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Mantener la interfaz original para compatibilidad
export interface PredictionData {
  [date: string]: {
    Predicted: number;
    Lower: number;
    Upper: number;
  };
}

// Actualizar la interfaz para que coincida con los datos del backend
export interface PredictionDataPoint {
  date: string;
  predicted: number;
  upper: number;
  lower: number;
}

interface PredictionChartProps {
  data: PredictionDataPoint[];
  currency?: string;
}

const PredictionChart: React.FC<PredictionChartProps> = ({ data, currency = '$' }) => {
  const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  const chartData = {
    labels: sortedData.map(d => d.date),
    datasets: [
      {
        label: 'Predicted Value',
        data: sortedData.map(d => d.predicted),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1,
      },
      {
        label: 'Upper Bound',
        data: sortedData.map(d => d.upper),
        borderColor: 'rgba(255, 99, 132, 0.5)',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        pointRadius: 0,
        tension: 0.1,
      },
      {
        label: 'Lower Bound',
        data: sortedData.map(d => d.lower),
        borderColor: 'rgba(255, 99, 132, 0.5)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderDash: [5, 5],
        pointRadius: 0,
        fill: '+1',
        tension: 0.1,
      },
    ],
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
        text: 'Price Prediction with Confidence Interval',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            let label = context.dataset.label || '';
            if (label) {
              label += `: ${currency}${context.parsed.y.toFixed(2)}`;
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: function(value: any) {
            return `${currency}${value}`;
          }
        }
      }
    }
  };

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

export default PredictionChart;
