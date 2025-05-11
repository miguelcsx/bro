"""
XGBoost-based volatility forecaster for stock market prediction
"""

import os 
import numpy as np
import pandas as pd
import warnings
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import RandomizedSearchCV
import xgboost
from src.ingestion.clients.yahoo import YahooFinanceClient

warnings.filterwarnings('ignore')

class XGBoostVolatility:
    """
    XGBoost volatility forecaster
    """
    
    def __init__(self, company, predict_col='Close', years_data=5, client=None):
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.model = None
        self.data = None
        self.forecast_results = None
        self.training_results = None
        self._load_data()

    def _generate_filename(self, file_type):
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_{self.predict_col}_{file_type}_{date_str}"
    
    def save_forecast(self):
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        os.makedirs('results', exist_ok=True)
        filename = self._generate_filename('forecast') + '.csv'
        filepath = os.path.join('results', filename)
        self.forecast_results.round(2).to_csv(filepath)
        print(f"Saved forecast to {filepath}")

    def _load_data(self):
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.years_data*365)
        
        df = self.client.get_historical_data(
            symbol=self.company,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        # Ensure we have a DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        self.data = df[[self.predict_col]].dropna()
        print(f"\nLoaded {len(self.data)} trading days of {self.predict_col} data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")

    def _compute_volatility(self, window=30):
        """
        rolling volatility (annualized)
        """
        returns = 100 * self.data[self.predict_col].pct_change().dropna()
        return np.sqrt(returns.rolling(window).var() * 252)

    def _create_features(self, df, target_series=None, include_target_lags=False):
        """
        feature engineering ofr training
        """
        features = pd.DataFrame(index=df.index)
        
        # Basic price transformations
        returns = 100 * df[self.predict_col].pct_change()
        features['returns'] = returns
        features['abs_returns'] = np.abs(returns)
        features['return_sign'] = np.sign(returns)
        
        # Technical indicators
        features['ma_10'] = df[self.predict_col].rolling(10).mean()
        features['ma_50'] = df[self.predict_col].rolling(50).mean()
        features['hi_lo'] = (df[self.predict_col].rolling(5).max() - 
                            df[self.predict_col].rolling(5).min())
        
        # Date features
        features['dayofweek'] = df.index.dayofweek
        features['quarter'] = df.index.quarter
        features['month'] = df.index.month
        features['dayofyear'] = df.index.dayofyear
        
        # Lagged features 
        if include_target_lags and target_series is not None:
            for i in range(1, 6): 
                features[f'vol_lag_{i}'] = target_series.shift(i)
        
        # Volatility regime features
        features['high_vol'] = (target_series > target_series.rolling(100).mean()).astype(int)
        
        return features.dropna()

    def forecast(self, days=30):
        """
        compute volatility with a window of 30 days
        """
        
        volatility = self._compute_volatility(window=30).dropna()
        
        # Split data properly
        test_size = int(len(volatility) * 0.2)
        train_vol = volatility[:-test_size]
        test_vol = volatility[-test_size:]
        
        
        X_train = self._create_features(self.data.loc[train_vol.index], train_vol, include_target_lags=True)
        y_train = train_vol.loc[X_train.index]  
        
        
        val_size = int(len(X_train) * 0.2)
        X_train_final = X_train[:-val_size]
        X_val = X_train[-val_size:]
        y_train_final = y_train[:-val_size]
        y_val = y_train[-val_size:]
        
        # hyperparameter tuning
        best_params = self._hyperparameter_tuning(X_train_final, y_train_final)
        
        # Train final model with validation set for early stopping
        self.model = xgboost.XGBRegressor(
            **best_params,
            early_stopping_rounds=50,
            eval_metric='rmse'
        )
        self.model.fit(
            X_train_final, 
            y_train_final,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Walk-forward validation for test set
        rolling_predictions = []
        history = self.data.loc[train_vol.index].copy()
        history_vol = train_vol.copy()
        
        for i in range(len(test_vol)):
            current_date = test_vol.index[i]
            
            
            X_test_step = self._create_features(
                pd.concat([history, self.data.loc[[current_date]]]),
                pd.concat([history_vol, test_vol.iloc[[i]]]),
                include_target_lags=True
            ).iloc[[-1]]
        
            pred = self.model.predict(X_test_step)[0]
            rolling_predictions.append(pred)
            
            history = pd.concat([history, self.data.loc[[current_date]]])
            history_vol = pd.concat([history_vol, test_vol.iloc[[i]]])
        
        
        self.training_results = pd.DataFrame({
            'True Volatility': test_vol,
            'Predicted Volatility': rolling_predictions
        }, index=test_vol.index)
        
        # Future forecast
        future_predictions = []
        forecast_data = self.data.copy()
        forecast_vol = volatility.copy()
        
        for i in range(days):
            last_date = forecast_data.index[-1]
            next_date = last_date + pd.offsets.BDay(1)
            
            
            X_future = self._create_features(
                forecast_data,
                forecast_vol,
                include_target_lags=True
            ).iloc[[-1]]
            
            # Predict volatility
            pred = self.model.predict(X_future)[0]
            future_predictions.append(pred)
            
            # Append a new row with predicted close
            new_row = forecast_data.iloc[[-1]].copy()
            new_row.index = [next_date]
            forecast_data = pd.concat([forecast_data, new_row])
            
            # Update volatility history
            new_vol = pd.Series([pred], index=[next_date])
            forecast_vol = pd.concat([forecast_vol, new_vol])
        
    
        future_dates = pd.date_range(
            start=self.data.index[-1] + pd.offsets.BDay(1),
            periods=days,
            freq='B'
        )
        
        self.forecast_results = pd.DataFrame({
            'Volatility': future_predictions,
            'Lower': np.array(future_predictions) * 0.9,
            'Upper': np.array(future_predictions) * 1.1
        }, index=future_dates)
        
        return self.forecast_results

    def _hyperparameter_tuning(self, X_train, y_train):
        """Enhanced parameter tuning"""
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [3, 4, 6],
            'learning_rate': [0.1, 0.05],
            'subsample': [0.8, 0.9, 1.0],
            'colsample_bytree': [1.0]
        }
        
        # Using randomized search for efficiency
        model = xgboost.XGBRegressor(objective='reg:squarederror', random_state=42)
        tscv = TimeSeriesSplit(n_splits=3)
        search = RandomizedSearchCV(
            model, param_grid, cv=tscv, n_iter=20,
            scoring='neg_root_mean_squared_error'
        )
        
        search.fit(X_train, y_train)
        print(f"Best params: {search.best_params_}")
        print(f"Best RMSE: {-search.best_score_:.4f}")
        
        return search.best_params_
    
    def get_forecast_dict(self):
        """
        Return the forecast results as a dictionary.
        The dictionary keys are the forecasted dates (as strings),
        and the values are dicts with 'Predicted', 'Lower', and 'Upper'.
        """
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
        
        # Convert index to string for JSON-friendly output
        forecast_dict = {
            str(idx.date()): {
                'Predicted': float(row['Volatility']),
                'Lower': float(row['Lower']),
                'Upper': float(row['Upper'])
            }
            for idx, row in self.forecast_results.iterrows()
        }
        return forecast_dict
    
    def evaluate(self):
        if self.training_results is None:
            raise ValueError("Run forecast() first")
        
        y_true = self.training_results['True Volatility']
        y_pred = self.training_results['Predicted Volatility']
        
        print(f"RMSE: {np.sqrt(mean_squared_error(y_true, y_pred)):.4f}")
        print(f"MAE: {mean_absolute_error(y_true, y_pred):.4f}")
        print(f"R²: {r2_score(y_true, y_pred):.4f}")

if __name__ == "__main__":
       model = XGBoostVolatility(company='AAPL')
       forecast = model.forecast(days=10)
       print(forecast)
