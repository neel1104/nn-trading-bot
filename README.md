# NN Trading Bot

A Python-based trading bot specialized in Market Structure (MS) and Price Action analysis.

## Features
- **Market Structure Analysis**: Identify Swing Highs, Swing Lows, and Break of Structure (BOS).
- **Inside Bar Filtering**: Automatically filter out inside bars for cleaner signals.
- **N-Candle Reversal Rule**: Custom logic to detect pivot points based on candle color reversals.
- **Interactive Visualization**: High-quality Plotly charts with BOS annotations and zoom capabilities.
- **Modular Pipeline**: Easy-to-use functional API for data processing and analysis.

## Getting Started

### Prerequisites
- **Python 3.13+**
- **Pipenv** (recommended for dependency management)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/neel1104/nn-trading-bot.git
   cd nn-trading-bot
   ```
2. Install dependencies using Pipenv:
   ```bash
   pipenv install
   ```

### Usage
You can run the analysis using the provided Jupyter notebook or by importing the `MarketStructureAnalyzer` in your script.

#### Using Jupyter Notebook
Open `playground.ipynb` and run all cells to see the BTC-USD market structure analysis.

#### Using Python Script
```python
import yfinance as yf
from market_structure import MarketStructureAnalyzer

# 1. Fetch Data
df = yf.download("BTC-USD", period="1y", interval="1wk")

# 2. Run Analysis
analyzer = (
    MarketStructureAnalyzer(df)
    .filter_inside_bars()
    .identify_pivots(min_candles=2)
    .find_bos()
)

# 3. Visualize
analyzer.plot(title="BTC-USD Weekly Structure")
```

## Project Structure
- `market_structure.py`: Core logic for market structure analysis.
- `playground.ipynb`: Example notebook demonstrating data fetching and visualization.
- `Pipfile`: Dependency specifications.

## Authors
- Neelesh
- Naveen

---
*Disclaimer: This is for educational purposes only. Trade at your own risk.*
