import React from 'react';

import { PredictionData } from './PredictionChart';

interface PredictionTableProps {
  data: PredictionData;
}

const PredictionTable: React.FC<PredictionTableProps> = ({ data }) => {
  const dates = Object.keys(data);

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
        {dates.map(date => (
          <tr key={date}>
            <td>{date}</td>
            <td>${data[date].Predicted.toFixed(2)}</td>
            <td>${data[date].Lower.toFixed(2)}</td>
            <td>${data[date].Upper.toFixed(2)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default PredictionTable;
