import numpy as np
import pandas as pd
import plotly.graph_objects as go


class MarketStructureAnalyzer:
    """
    A modular analyzer for Market Structure (MS) and Price Action.
    Uses N-candle color reversals to identify swing points and structure breaks
    (BOS).

    Pipeline:
    Analyzer(df).filter_inside_bars().identify_pivots().find_bos().plot()
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Clean data: drop NaNs and ensure numeric
        self.df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        for col in ["Open", "High", "Low", "Close"]:
            self.df[col] = pd.to_numeric(self.df[col])

        self.df_valid = None
        self.df_pivots = None
        self.bos_events = []

    def filter_inside_bars(self) -> "MarketStructureAnalyzer":
        """
        Identifies and filters out inside bars and flags them in self.df.
        An inside bar is: High <= Prev High AND Low >= Prev Low.
        """
        if self.df.empty:
            return self

        self.df["is_inside"] = False
        valid_indices = [self.df.index[0]]
        last_valid_high = self.df["High"].iloc[0]
        last_valid_low = self.df["Low"].iloc[0]

        for i in range(1, len(self.df)):
            curr_high = self.df["High"].iloc[i]
            curr_low = self.df["Low"].iloc[i]

            # Inside bar check (relative to last valid bar)
            is_inside = (curr_high <= last_valid_high) and (
                curr_low >= last_valid_low
            )

            if not is_inside:
                valid_indices.append(self.df.index[i])
                last_valid_high = curr_high
                last_valid_low = curr_low
            else:
                self.df.at[self.df.index[i], "is_inside"] = True

        self.df_valid = self.df.loc[valid_indices].copy()
        print(f"Filtered inside bars: {len(self.df)} -> {len(self.df_valid)}")
        return self

    def identify_pivots(self, min_candles=2) -> "MarketStructureAnalyzer":
        """
        Identifies Pivot Highs and Lows based on color reversals.
        The reversal condition is met when 'min_candles' of the opposite
        color appear in sequence.
        """
        if self.df_valid is None:
            self.filter_inside_bars()

        df = self.df_valid.copy()
        df["is_green"] = df["Close"] > df["Open"]
        df["is_red"] = df["Close"] < df["Open"]

        df["pivot_high"] = np.nan
        df["pivot_low"] = np.nan
        df["label"] = ""

        trend = None  # 'bull' or 'bear'
        current_trend_start_idx = 0

        for i in range(1, len(df)):
            # Check for Bullish Reversal (N consecutive green)
            if trend != "bull" and all(
                df["is_green"].iloc[i - j] for j in range(min_candles)
            ):
                if trend == "bear":
                    search_range = df.iloc[current_trend_start_idx:i + 1]
                    low_idx = search_range["Low"].idxmin()
                    df.at[low_idx, "pivot_low"] = search_range["Low"].min()

                trend = "bull"
                current_trend_start_idx = i - (min_candles - 1)

            # Check for Bearish Reversal (N consecutive red)
            elif trend != "bear" and all(
                df["is_red"].iloc[i - j] for j in range(min_candles)
            ):
                if trend == "bull":
                    search_range = df.iloc[current_trend_start_idx:i + 1]
                    high_idx = search_range["High"].idxmax()
                    df.at[high_idx, "pivot_high"] = search_range["High"].max()

                trend = "bear"
                current_trend_start_idx = i - (min_candles - 1)

        # Add labels (HH, HL, LH, LL)
        self._add_labels(df)
        self.df_pivots = df
        return self

    def _add_labels(self, df):
        """
        Internal helper to assign market structure labels based on previous
        swing points: HH: Higher High, LH: Lower High, HL: Higher Low,
        LL: Lower Low.
        """
        # Highs
        highs = df[df["pivot_high"].notna()]["pivot_high"]
        if not highs.empty:
            labels = ["H"]
            for i in range(1, len(highs)):
                labels.append(
                    "HH" if highs.iloc[i] > highs.iloc[i - 1] else "LH"
                )
            df.loc[highs.index, "label"] = labels

        # Lows
        lows = df[df["pivot_low"].notna()]["pivot_low"]
        if not lows.empty:
            labels = ["L"]
            for i in range(1, len(lows)):
                labels.append(
                    "HL" if lows.iloc[i] > lows.iloc[i - 1] else "LL"
                )
            for idx, lbl in zip(lows.index, labels):
                df.at[idx, "label"] = lbl

    def find_bos(self) -> "MarketStructureAnalyzer":
        """
        Detects Break of Structure (BOS) using price close.
        Classifies BOS as 'good' or 'bad' based on whether the next candle
        also closes above/below the broken level.
        """
        if self.df_pivots is None:
            self.identify_pivots()

        df = self.df_pivots
        last_ph_idx, last_ph_val = None, None
        last_pl_idx, last_pl_val = None, None
        self.bos_events = []

        for i in range(len(df)):
            curr_idx = df.index[i]
            curr_close = df["Close"].iloc[i]

            if not pd.isna(df["pivot_high"].iloc[i]):
                last_ph_idx, last_ph_val = curr_idx, df["pivot_high"].iloc[i]
            if not pd.isna(df["pivot_low"].iloc[i]):
                last_pl_idx, last_pl_val = curr_idx, df["pivot_low"].iloc[i]

            if last_ph_val and curr_close > last_ph_val:
                quality = "bad"
                if i + 1 < len(df):
                    next_close = df["Close"].iloc[i + 1]
                    if next_close > last_ph_val:
                        quality = "good"

                self.bos_events.append(
                    {
                        "start_date": last_ph_idx,
                        "end_date": curr_idx,
                        "level": last_ph_val,
                        "type": "BOS",
                        "color": "green",
                        "quality": quality,
                    }
                )
                last_ph_val = None

            elif last_pl_val and curr_close < last_pl_val:
                quality = "bad"
                if i + 1 < len(df):
                    next_close = df["Close"].iloc[i + 1]
                    if next_close < last_pl_val:
                        quality = "good"

                self.bos_events.append(
                    {
                        "start_date": last_pl_idx,
                        "end_date": curr_idx,
                        "level": last_pl_val,
                        "type": "BOS",
                        "color": "red",
                        "quality": quality,
                    }
                )
                last_pl_val = None
        return self

    def plot(
        self,
        title: str = "Market Structure Analysis",
        zoom_days: int = 30,
        output_path: str = None,
    ):
        df = self.df
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="Price",
                )
            ]
        )

        # 1. Plot Pivots
        if self.df_pivots is not None:
            df_pivots = self.df_pivots
            highs = df_pivots[df_pivots["pivot_high"].notna()]
            lows = df_pivots[df_pivots["pivot_low"].notna()]

            fig.add_trace(
                go.Scatter(
                    x=highs.index,
                    y=highs["pivot_high"],
                    mode="markers+text",
                    text=highs["label"],
                    textposition="top center",
                    marker=dict(
                        color="green", size=10, symbol="triangle-down"
                    ),
                    name="Swing Highs",
                    textfont=dict(color="green", size=11),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=lows.index,
                    y=lows["pivot_low"],
                    mode="markers+text",
                    text=lows["label"],
                    textposition="bottom center",
                    marker=dict(color="red", size=10, symbol="triangle-up"),
                    name="Swing Lows",
                    textfont=dict(color="red", size=11),
                )
            )

        # 2. Plot BOS Lines
        for bos in self.bos_events:
            line_dash = "solid" if bos.get("quality") == "good" else "dot"
            fig.add_shape(
                type="line",
                x0=bos["start_date"],
                y0=bos["level"],
                x1=bos["end_date"],
                y1=bos["level"],
                line=dict(color=bos["color"], width=1, dash=line_dash),
            )
            fig.add_annotation(
                x=bos["end_date"],
                y=bos["level"],
                text=f"BOS ({bos.get('quality', 'N/A')[0]})",
                showarrow=False,
                yshift=10 if bos["color"] == "green" else -10,
                font=dict(color=bos["color"], size=9),
            )

        # 3. Plot Inside Bars
        if "is_inside" in df.columns:
            inside_bars = df[df["is_inside"]]
            if not inside_bars.empty:
                # Nudge the dot 0.5% above candle high for visibility
                fig.add_trace(
                    go.Scatter(
                        x=inside_bars.index,
                        y=inside_bars["High"] * 1.005,
                        mode="markers",
                        marker=dict(color="gray", size=5, symbol="circle"),
                        name="Inside Bar",
                    )
                )

        # Layout & Zoom
        start_date = df.index[0]
        end_zoom = start_date + pd.Timedelta(days=zoom_days)

        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=True,
            template="plotly_white",
            xaxis=dict(range=[start_date, end_zoom]),
            height=800,
        )

        if output_path:
            fig.write_image(output_path)
        else:
            fig.show()
