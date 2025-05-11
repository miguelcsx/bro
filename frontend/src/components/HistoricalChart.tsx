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
import { Line } from 'react-chartjs-2';
import React from 'react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export interface HistoricalDataPoint {
  date: string;
  price: number;
}

interface HistoricalChartProps {
  data: HistoricalDataPoint[];
  currency?: string;
}

const HistoricalChart: React.FC<HistoricalChartProps> = ({ data, currency = '$' }) => {
  const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  const chartData = {
    labels: sortedData.map(d => d.date),
    datasets: [
      {
        label: 'Historical Price',
        data: sortedData.map(d => d.price),
        borderColor: '#3182ce',
        backgroundColor: 'rgba(49, 130, 206, 0.1)',
        borderWidth: 2,
        pointRadius: 2,
        pointHoverRadius: 5,
        fill: true,
        tension: 0.2,
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
        text: 'Historical Stock Price',
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `Price: ${currency}${context.parsed.y.toFixed(2)}`;
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

export default HistoricalChart; 