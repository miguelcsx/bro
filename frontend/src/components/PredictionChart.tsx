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

export interface PredictionData {
  [date: string]: {
    Predicted: number;
    Lower: number;
    Upper: number;
  };
}

interface PredictionChartProps {
  data: PredictionData;
}

const PredictionChart: React.FC<PredictionChartProps> = ({ data }) => {
  const dates = Object.keys(data);
  const chartData = {
    labels: dates,
    datasets: [
      {
        label: 'Predicted Value',
        data: dates.map(date => data[date].Predicted),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
      {
        label: 'Confidence Interval',
        data: dates.map(date => data[date].Upper),
        borderColor: 'rgba(255, 99, 132, 0.2)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
      },
    ],
  };

  return <Line data={chartData} />;
};

export default PredictionChart;
