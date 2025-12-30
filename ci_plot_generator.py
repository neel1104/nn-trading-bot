import yfinance as yf
import pandas as pd
from market_structure import MarketStructureAnalyzer

# 1. Fetch Data
ticker = "BTC-USD"
df = yf.download(ticker, period="1y", interval="1wk")
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(1)

# 2. Run Functional Pipeline
analyzer = (
    MarketStructureAnalyzer(df)
    .filter_inside_bars()
    .identify_pivots(min_candles=2)
    .find_bos()
)

# 3. Generate and Save the Plot
output_filename = "market_structure_plot.png"
analyzer.plot(
    title=f"{ticker} Market Structure (2-2-2 Rule)",
    zoom_days=52,
    output_path=output_filename,
)

print(f"Plot saved to {output_filename}")
