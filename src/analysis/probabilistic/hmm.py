import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from hmmlearn.hmm import GaussianHMM
import itertools
from tqdm import tqdm
from sklearn.model_selection import train_test_split
import os

from src.ingestion.clients.yahoo import YahooFinanceClient


class HMMModel:
    """
    HMMModel forecaster using YahooFinanceClient for data access
    """
    
    def __init__(self, company, predict_col='Close', years_data=5, client=None):
        self.company = company
        self.predict_col = predict_col
        self.years_data = years_data
        self.client = client or YahooFinanceClient()
        self.model = None
        self.data = None
        self.forecast_results = None
        self.n_components_options = [5, 10, 15]
        self.best_n_components = None
        self._load_data()

    def _generate_filename(self, file_type):
        """Generate standardized filenames"""
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.company}_{self.predict_col}_{file_type}_{date_str}"
    
    def save_forecast(self):
        """Save forecast results to CSV"""
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        filename = self._generate_filename('forecast') + '.csv'
        filepath = os.path.join('results', filename)
        self.forecast_results.round(2).to_csv(filepath)
        print(f"Saved forecast to {filepath}")
        
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
        
        # Validate and store ALL required columns
        required_cols = ['Open', 'High', 'Low', 'Close']
        for col in required_cols:
            if col not in df.columns:
                available = ', '.join(df.columns)
                raise ValueError(f"Column '{col}' not found. Available: {available}")
                
        self.data = df[required_cols].dropna()  # Store all required columns

    def _augment_features(self, dataframe):
        """
        create percentage change for features for prediction
        """

        fracocp = (dataframe['Close']-dataframe['Open'])/dataframe['Open']
        frachp = (dataframe['High']-dataframe['Open'])/dataframe['Open']
        fraclp = (dataframe['Open']-dataframe['Low'])/dataframe['Open']
        new_dataframe = pd.DataFrame({'delOpenClose': fracocp,
                                    'delHighOpen': frachp,
                                    'delLowOpen': fraclp})
        new_dataframe.set_index(dataframe.index)
        
        return new_dataframe


    def _make_combinations(self, test_data):
        """
        create a grid of plausible future movements for the stock
        """

        test_augmented = self._augment_features(test_data)
        fracocp = test_augmented['delOpenClose']
        frachp = test_augmented['delHighOpen']
        fraclp = test_augmented['delLowOpen']

        sample_space_fracocp = np.linspace(fracocp.min(), fracocp.max(), 50)
        sample_space_fraclp = np.linspace(fraclp.min(), frachp.max(), 10)
        sample_space_frachp = np.linspace(frachp.min(), frachp.max(), 10)

        possible_outcomes = np.array(list(itertools.product(sample_space_fracocp, sample_space_frachp, sample_space_fraclp)))

        return possible_outcomes
    

    def _tune_hyperparameters(self, features, test_size=0.2):
        """
        find best number of hidden states using validation set
        """
        X_train, X_val = train_test_split(features, test_size=test_size, shuffle=False, random_state=42)
        best_score = -np.inf
        best_n = None
        best_model = None  # Store the best model

        for n in self.n_components_options:
            try:
                model = GaussianHMM(
                    n_components=n, 
                    covariance_type="diag", 
                    n_iter=2000,
                    tol=0.05,
                    init_params='st'
                )
                model.fit(X_train)
                score = model.score(X_val)

                if score > best_score:
                    best_score = score
                    best_n = n
                    best_model = model  # Store the best model
                    print(f"New best n_components={n} with score of {score:.2f}")
            except Exception as e:
                print(f"Skipping n_components={n}: {str(e)}")
                continue

        if best_n is None:
            raise ValueError("No valid HMM model found during tuning")
        
        self.best_n_components = best_n
        print(f"\nSelected n_components={best_n} as optimal")
        return best_model 


    def forecast(self, days=30, lookback_window = 30):
        """
        generate bussiness day forecast
        """

        augmented_data = self._augment_features(self.data)
        features = np.column_stack((
            augmented_data["delOpenClose"],
            augmented_data["delHighOpen"],
            augmented_data["delLowOpen"]
        ))

        #best_n = self._tune_hyperparameters(features)

        self.model = self._tune_hyperparameters(features)

        predicted_prices = []; lower_bounds = []; upper_bounds = []
        last_window = self.data.iloc[-lookback_window:]

        for _ in tqdm(range(days), desc="Forecasting"):
            possible_outcomes = self._make_combinations(last_window)
            window_features = np.column_stack((
                (last_window['Close'] - last_window['Open']) / last_window['Open'],
                (last_window['High'] - last_window['Open']) / last_window['Open'],
                (last_window['Open'] - last_window['Low']) / last_window['Open']
            ))

            outcome_scores = []
            for outcome in possible_outcomes:
                total_data = np.vstack((window_features, outcome))
                outcome_scores.append(self.model.score(total_data))
            
            most_probable = possible_outcomes[np.argmax(outcome_scores)]
            predicted_change = most_probable[0]

            last_price = last_window["Close"].iloc[-1]
            predicted_price = last_price * (1+ predicted_change)

            # Store results with simple confidence intervals
            predicted_prices.append(predicted_price)
            lower_bounds.append(predicted_price * 0.98)  # 2% below
            upper_bounds.append(predicted_price * 1.02)  # 2% above

            # Update window for next prediction
            new_row = last_window.iloc[-1:].copy()
            new_row['Open'] = last_price
            new_row['Close'] = predicted_price
            new_row['High'] = last_price * (1 + most_probable[1])
            new_row['Low'] = last_price * (1 - most_probable[2])
            
            last_window = pd.concat([last_window.iloc[1:], new_row])

        last_date = self.data.index[-1]
        future_dates = pd.date_range(
            start=last_date + pd.offsets.BDay(1),
            periods=days,
            freq="B"
        )

        self.forecast_results = pd.DataFrame({
            'Predicted': predicted_prices,
            'Lower': lower_bounds,
            'Upper': upper_bounds
        }, index=future_dates)
        
        return self.forecast_results
    

    def show_forecast(self):
        """
        Display the forecast results in a clean tabular format
        """
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")
            
        print(f"\n{'='*50}")
        print(f"{self.company} {self.predict_col} Price Forecast")
        print(f"Hidden Markov Model (n_components={self.best_n_components})")
        print(f"Forecast Period: {len(self.forecast_results)} business days")
        print(f"Last Historical Date: {self.data.index[-1].strftime('%Y-%m-%d')}")
        print(f"Last Historical Price: ${self.data['Close'].iloc[-1]:.2f}")
        print('='*50)
        
        # Create a formatted table
        forecast_df = self.forecast_results.copy()
        forecast_df.index = forecast_df.index.strftime('%Y-%m-%d')
        forecast_df['Predicted'] = forecast_df['Predicted'].apply(lambda x: f"${x:.2f}")
        forecast_df['Range'] = forecast_df.apply(
            lambda x: f"${x['Lower']:.2f}-${x['Upper']:.2f}", axis=1
        )
        
        # Print the table with headers
        print("\nDate\t\tPredicted\tConfidence Range")
        print("-"*50)
        for date, row in forecast_df.iterrows():
            print(f"{date}\t{row['Predicted']}\t{row['Range']}")
        
        print('='*50)
        print(f"Note: Confidence range represents ±2% from predicted value\n")

    def plot(self, show=True):
        """Generate and save forecast plot with improved styling"""
        if self.forecast_results is None:
            raise ValueError("Run forecast() first")

        # First show the numerical forecast
        self.show_forecast()

        plt.figure(figsize=(14, 7))
        
    
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
                'Predicted': float(row['Predicted']),
                'Lower': float(row['Lower']),
                'Upper': float(row['Upper'])
            }
            for idx, row in self.forecast_results.iterrows()
        }
        return forecast_dict
    

# if __name__ == "__main__":
#       model = HMMModel(company='AAPL')
#       forecast = model.forecast(days=10)
#       print(forecast)
