import React from 'react';

interface VisualizationProps {
  type: 'image' | 'svg' | 'plotly';
  data: string;
  format?: string;
}

const VisualizationComponent: React.FC<VisualizationProps> = ({ type, data, format }) => {
  if (type === 'image') {
    return <img src={`data:image/${format || 'png'};base64,${data}`} 
                alt="Model Visualization" 
                style={{ maxWidth: '100%', height: 'auto' }} />;
  }
  
  if (type === 'svg') {
    return <div dangerouslySetInnerHTML={{ __html: data }} />;
  }
  
  return null;
};

export default VisualizationComponent;