# Bro: Financial Assistant

![logo](logo.jpeg)

Build to simplify complex financial data and help you make smarter decisions, faster.

## How to Use It

1. **Launch the application** by following the installation instructions or using Docker Compose (see below).
2. **Access the web interface** at [http://localhost:3000](http://localhost:3000).
3. In the chat box, enter your questions about stocks, for example:
   - "What will be Google's closing price tomorrow?"
   - "Predict Tesla's stock using LSTM with 3 years of data."
   - "Forecast Amazon's price for next week."
4. The assistant will respond with analysis, predictions, and interactive charts.
5. You can query different companies, models, and time periods.

---

## Features

- AI-powered financial assistant  
- Real-time stock predictions using various Probabilistic, Deep Learning and Timeseries-Forecasting models  
- Volatility models for measuring risk  
- Checking for overbought or oversale behavior in stocks  
- Interactive stock visualization  
- Chat interface for natural language queries  

## Models Implemented

Several models were used for achieving this task. These are:

### For Forecasting Prediction (Stock Prices)

**Probabilistic models:**  
- ARIMA  
- Hidden Markov Model  
- Kalman Filter  

**Deep Learning models:**  
- Long-Short Term Memory (LSTM)  

**Time Series models:**  
- Facebook Prophet (FBProphet)  

### For Volatility Prediction (Rate Changes)

- Generalized Autoregressive Conditional Heteroskedasticity Model (GARCH)  
- XGBoost model for volatility  

### For Detecting Overbought/Oversold Behavior

- RSI index  

### For Detecting Up and Down Probabilities

Supervised machine learning algorithms were implemented for classification tasks to reach a "consensus" between models and predict with high truth if the stock will be up or down. These models include:

- Logistic Regression  
- XGBoost  
- Random Forest  
- LightGBM  
- CatBoost  
- AdaBoost  

## Architecture

The application consists of two main components:

1. **Python Backend**
    - LangChain-based AI agent with quantitative analysis tools  
    - FastAPI server exposing the agent as an API  
    - Connects to MCP (Model Context Protocol) servers for various prediction models  

2. **Next.js Frontend**
    - Modern React UI with Assistant UI components  
    - Stock visualization with Recharts  
    - Real-time chat interface  

## Setup

### Prerequisites

- Python 3.10+  
- Node.js 18+  
- npm or yarn  

### Installation

1. **Install Python dependencies**
    ```
    # Create a virtual environment (optional but recommended)
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```

2. **Install JavaScript dependencies**
    ```
    cd frontend
    npm install
    ```

### Running the Application

1. **Start the MCP server**
    ```
    poetry run python -m src.mcp.main
    ```

2. **Start the FastAPI server**
    ```
    poetry run python -m src.main
    ```

3. **Start the Next.js frontend**
    ```
    cd app
    npm start
    ```

4. Visit [http://localhost:3000](http://localhost:3000) to use the application

## Usage

You can ask the assistant questions about stocks, such as:

- "What will be the closing price for Google stock tomorrow?"  
- "Can you predict Tesla stock using LSTM with 3 years of data?"  
- "Forecast Amazon stock price for next week"  

## Api Key

In order to use Bro on your local machine, you must create a `.env` file and set the `GEMINI_API_KEY=api_key variable`. For the development of this project, we used a free trial Gemini API key. We want you to be able to use it as well, so we've created a new Gemini API key with a free trial (note: this means only a limited number of questions and attempts are allowed before reaching the token limit). However, it is perfectly suitable for trying out Bro. The api key is: `AIzaSyDOqUQzvkNoDPgFZVggPTTa55eXvAZhP9Y, we provide you this in order to test it easily. 
We know this seems unsafe, but it is only for community use.

## References

As we mentioned, Bro was built using several scientific research papers where different models were tried and proven. You can find them in the [`references`](./references). directory.

The assistant will use the appropriate prediction model and display the results in both text form and as visualizations in the chart area.
