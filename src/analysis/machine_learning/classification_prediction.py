import os
import numpy as np
import pandas as pd
import warnings
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
from src.ingestion.clients.yahoo import YahooFinanceClient

warnings.filterwarnings('ignore')

class StockDirectionPredictor:
    """
    Stock direction predictor using multiple ML models with YahooFinance data
    """
    
    def __init__(self, company, predict_col='Close', years_data=5, client=None):
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.models = None
        self.data = None
        self.features = None
        self._load_data()
        self._prepare_data()
    
    def _generate_filename(self, file_type):
        """Generate standardized filenames"""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_{self.predict_col}_{file_type}_{date_str}"
    
    def save_predictions(self, predictions):
        """Save prediction results to CSV"""
        filename = self._generate_filename('predictions') + '.csv'
        filepath = os.path.join('results', filename)
        predictions.to_csv(filepath)
        print(f"Saved predictions to {filepath}")
    
    def _load_data(self):
        """Load historical data using YahooFinanceClient"""
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.years_data*365)
        
        # Get data from client
        df = self.client.get_historical_data(
            symbol=self.company,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d'
        )
        
        if df is None or df.empty:
            raise ValueError(f"No historical data found for symbol '{self.company}'")
            
        if self.predict_col not in df.columns:
            available = ', '.join(df.columns)
            raise ValueError(f"Column '{self.predict_col}' not found. Available: {available}")
            
        self.data = df.copy()
        
        print(f"\nLoaded {len(self.data)} trading days of data")
        print(f"Date range: {self.data.index[0].date()} - {self.data.index[-1].date()}")
    
    def _add_technical_features(self, df):
        """Add technical analysis features"""
        df = df.copy()
        
        # Create target
        df['sma5'] = df['Close'].rolling(5).mean()
        df['target'] = np.where(
            (df['sma5'].shift(-1) > df['sma5']*1.002) & 
            (df['Close'].shift(-1) > df['Close']*1.001),
            1, 0)
        
        # Price transformations
        df['returns'] = df['Close'].pct_change()
        df['log_returns'] = np.log(df['Close']/df['Close'].shift(1))
        
        # Lagged returns and prices
        for lag in [1, 2, 3, 5, 10, 20]:
            df[f'return_lag_{lag}'] = df['returns'].shift(lag)
            df[f'close_lag_{lag}'] = df['Close'].shift(lag)
        
        # Price action features
        df['O-C'] = df['Open'] - df['Close']
        df['H-L'] = df['High'] - df['Low']
        df['C-PrevC'] = df['Close'] - df['Close'].shift(1)
        
        # Volume features
        df['volume_change'] = df['Volume'].pct_change()
        df['volume_ma_10'] = df['Volume'].rolling(10).mean()
        df['volume_ma_20'] = df['Volume'].rolling(20).mean()
        
        # Momentum indicators
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # Stochastic %K
        low_min = df['Low'].rolling(14).min()
        high_max = df['High'].rolling(14).max()
        df['stoch_k'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        
        # Trend indicators
        for window in [10, 20, 50, 200]:
            df[f'sma_{window}'] = df['Close'].rolling(window).mean()
            df[f'ema_{window}'] = df['Close'].ewm(span=window, adjust=False).mean()
            df[f'close_sma_ratio_{window}'] = df['Close'] / df[f'sma_{window}']
            df[f'close_ema_ratio_{window}'] = df['Close'] / df[f'ema_{window}']
        
        # Volatility indicators
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['Close'].rolling(20).mean()
        df['bb_upper'] = df['bb_middle'] + 2 * df['Close'].rolling(20).std()
        df['bb_lower'] = df['bb_middle'] - 2 * df['Close'].rolling(20).std()
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        # Remove rows with missing values
        df.dropna(inplace=True)
        
        return df
    
    def _feature_selection(self, df, top_n=30):
        """
        Select best features using multiple methods
        """
        exclude_cols = ['target', 'sma5']
        features = [col for col in df.columns 
                   if col not in exclude_cols 
                   and pd.api.types.is_numeric_dtype(df[col])]
        
        X = df[features]
        y = df['target']
        
        # Correlation
        corr = X.corrwith(y).abs().sort_values(ascending=False)
        corr_features = corr.head(top_n).index.tolist()
        
        # ANOVA
        selector_f = SelectKBest(score_func=f_classif, k=top_n)
        selector_f.fit(X, y)
        f_features = X.columns[selector_f.get_support()].tolist()
        
        # Mutual Information
        selector_mi = SelectKBest(score_func=mutual_info_classif, k=top_n)
        selector_mi.fit(X, y)
        mi_features = X.columns[selector_mi.get_support()].tolist()
        
        # Find consensus features
        all_features = corr_features + f_features + mi_features
        feature_counts = pd.Series(all_features).value_counts()
        selected_features = feature_counts[feature_counts >= 2].index.tolist()
        
        # If not enough consensus, take top from correlation
        if len(selected_features) < top_n:
            remaining = top_n - len(selected_features)
            selected_features.extend(corr_features[:remaining])
        
        return selected_features[:top_n]
    
    def _prepare_data(self):
        """Prepare data for modeling"""
        df = self._add_technical_features(self.data)
        self.features = self._feature_selection(df)
        self.data = df
    
    def _train_models(self):
        """Train ensemble of models"""
        X = self.data[self.features]
        y = self.data['target']
        
        
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]
        
        
        classifiers = [
            ('Logistic Regression', LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced')),
            ('AdaBoost', AdaBoostClassifier(random_state=42, n_estimators=200)),
            ('CatBoost', CatBoostClassifier(random_state=42, verbose=False, iterations=300)),
            ('XGBoost', XGBClassifier(random_state=42, eval_metric='logloss')),
            ('LightGBM', LGBMClassifier(random_state=42)),
            ('Random Forest', RandomForestClassifier(random_state=42, class_weight='balanced'))
        ]
        
        # Train and select best model based on validation AUC
        best_auc = 0
        best_model = None
        trained_models = []
        
        for name, clf in classifiers:
            print(f"Training {name}...")
            clf.fit(X_train, y_train)
            y_proba = clf.predict_proba(X_val)[:, 1]
            auc = roc_auc_score(y_val, y_proba)
            trained_models.append((name, clf, auc))
            
            if auc > best_auc:
                best_auc = auc
                best_model = (name, clf)
            
            print(f"{name} validation AUC: {auc:.4f}")
        
        print(f"\nBest model: {best_model[0]} with AUC: {best_auc:.4f}")
        self.models = trained_models
    
    def predict_direction(self, days=1):
        """
        Predict probability of stock going up/down
        """
        if not self.models:
            self._train_models()
        
        
        latest_data = self.data.iloc[-1][self.features].values.reshape(1, -1)
        model_predictions = {}
        for name, model, auc in self.models:
            proba = model.predict_proba(latest_data)[0]
            model_predictions[name] = {
                'up_prob': float(proba[1]),
                'down_prob': float(proba[0]),
                'auc': float(auc)
            }
        
        # Calculate consensus prediction (weighted by model AUC)
        total_auc = sum(m[2] for m in self.models)
        consensus_up = sum(model_predictions[name]['up_prob'] * (auc/total_auc) 
                         for name, _, auc in self.models)
        
        result = {
            'date': str(datetime.now().date()),
            'prediction_days': days,
            'consensus': {
                'up_prob': consensus_up,
                'down_prob': 1 - consensus_up
            },
            'models': model_predictions
        }
        
        pred_df = pd.DataFrame.from_dict({
            name: {
                'Up Probability': pred['up_prob'],
                'Down Probability': pred['down_prob'],
                'Model AUC': pred['auc']
            }
            for name, pred in model_predictions.items()
        }, orient='index')
        
        pred_df.loc['Consensus'] = {
            'Up Probability': consensus_up,
            'Down Probability': 1 - consensus_up,
            'Model AUC': None
        }
        
        self.save_predictions(pred_df)
        
        return result

    def get_prediction_dict(self):
        """
        Return the prediction results
        """
        return self.predict_direction()
    
# if __name__ == "__main__":
#      predictor = StockDirectionPredictor(company='AAPL', years_data=3)
    
#      predictions = predictor.predict_direction(days=1)
#      print(predictions)