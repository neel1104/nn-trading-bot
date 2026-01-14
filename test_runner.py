import yfinance as yf
import pandas as pd
from market_structure import MarketStructureAnalyzer

# 1. Fetch Data
ticker = "BTC-USD"
# Use a shorter period to speed up the test
df = yf.download(ticker, period="1y", interval="1wk")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

# 2. Run Functional Pipeline
analyzer = (
    MarketStructureAnalyzer(df)
    .filter_inside_bars()
    .identify_pivots(min_candles=2)
    .find_bos()
    .with_candlestick_patterns()
)

# 3. Visualize
# The plot won't be displayed in the terminal, but this will ensure the code runs without errors.
analyzer.plot(title=f"{ticker} Market Structure (2-2-2 Rule)", zoom_days=52)

print("Test script executed successfully.")
