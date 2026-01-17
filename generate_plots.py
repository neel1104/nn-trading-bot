import yfinance as yf
import pandas as pd
from market_structure import MarketStructureAnalyzer
import os

def generate_plot(ticker, period, interval, filename, with_patterns=False):
    """
    Generates and saves a market structure plot.
    """
    df = yf.download(ticker, period=period, interval=interval)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    analyzer = (
        MarketStructureAnalyzer(df)
        .filter_inside_bars()
        .identify_pivots(min_candles=2)
        .find_bos()
    )

    if with_patterns:
        analyzer.with_candlestick_patterns()

    title = f"{ticker} Market Structure ({period}, {interval})"
    if with_patterns:
        title += " with Candlestick Patterns"
    analyzer.plot(title=title, zoom_days=365, filepath=filename)
    print(f"Generated plot: {filename}")

def main():
    """
    Main function to generate all plots and the index.html.
    """
    if not os.path.exists("docs"):
        os.makedirs("docs")

    plots = [
        {"ticker": "BTC-USD", "period": "1y", "interval": "1wk", "filename": "docs/btc-usd_weekly.html", "with_patterns": False},
        {"ticker": "BTC-USD", "period": "1y", "interval": "1d", "filename": "docs/btc-usd_daily.html", "with_patterns": False},
        {"ticker": "BTC-USD", "period": "1y", "interval": "1wk", "filename": "docs/btc-usd_weekly_patterns.html", "with_patterns": True},
        {"ticker": "BTC-USD", "period": "1y", "interval": "1d", "filename": "docs/btc-usd_daily_patterns.html", "with_patterns": True},
    ]

    for plot in plots:
        generate_plot(plot["ticker"], plot["period"], plot["interval"], plot["filename"], plot["with_patterns"])

    with open("docs/index.html", "w") as f:
        f.write("<html><head><title>Market Structure Plots</title></head><body>\n")
        f.write("<h1>Market Structure Plots</h1>\n")
        f.write("<ul>\n")
        for plot in plots:
            f.write(f'<li><a href="{os.path.basename(plot["filename"])}">{plot["ticker"]} ({plot["period"]}, {plot["interval"]})</a></li>\n')
        f.write("</ul>\n")
        f.write("</body></html>\n")
    print("Generated index.html")

if __name__ == "__main__":
    main()
