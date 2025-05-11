module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  settings: {
    'import/resolver': {
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx']
      }
    }
  },
  rules: {
    'import/no-unresolved': [
      2, 
      { ignore: ['^chart.js$', '^react-chartjs-2$'] }
    ]
  }
}; 