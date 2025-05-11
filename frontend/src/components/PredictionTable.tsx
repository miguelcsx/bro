import React from 'react';
import { PredictionData, PredictionDataPoint } from './PredictionChart';

interface PredictionTableProps {
  data: PredictionData | PredictionDataPoint[];
}

const PredictionTable: React.FC<PredictionTableProps> = ({ data }) => {
  // Verificar qué formato de datos tenemos y convertirlo si es necesario
  const isArrayFormat = Array.isArray(data);
  
  // Si es un array, asumimos que es PredictionDataPoint[]
  const tableData = isArrayFormat 
    ? data.map((item: PredictionDataPoint) => ({
        date: item.date,
        predicted: item.predicted,
        upper: item.upper,
        lower: item.lower
      }))
    : Object.keys(data).map(date => ({
        date,
        predicted: data[date].Predicted,
        upper: data[date].Upper,
        lower: data[date].Lower
      }));
  
  // Ordenar por fecha
  const sortedData = [...tableData].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  return (
    <table className="prediction-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Predicted</th>
          <th>Lower</th>
          <th>Upper</th>
        </tr>
      </thead>
      <tbody>
        {sortedData.map(item => (
          <tr key={item.date}>
            <td>{item.date}</td>
            <td>${item.predicted.toFixed(2)}</td>
            <td>${item.lower.toFixed(2)}</td>
            <td>${item.upper.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default PredictionTable;
