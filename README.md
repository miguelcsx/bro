# Financial Assistant

Built to simplify complex financial data and help you make smarter decisions, faster.

## Features

- AI-powered financial assistant
- Real-time stock predictions using various models (LSTM, ARIMA, Prophet, HMM)
- Interactive stock visualization
- Chat interface for natural language queries

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
   cd app
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
    npm run dev
    ```

4. Visit http://localhost:3000 to use the application

## Usage

You can ask the assistant questions about stocks, such as:

- "What will be the closing price for Google stock tomorrow?"
- "Can you predict Tesla stock using LSTM with 3 years of data?"
- "Forecast Amazon stock price for next week"

The assistant will use the appropriate prediction model and display the results in both text form and as visualizations in the chart area.
