import pandas as pd
from typing import Optional


class CandlestickPatternIdentifier:
    """
    A class to identify various candlestick patterns in a given OHLCV DataFrame.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initializes the CandlestickPatternIdentifier with a DataFrame.

        :param df: pd.DataFrame with columns ['Open', 'High', 'Low', 'Close']
        """
        self.df = df
        self.df['candlestick_pattern'] = None

    def identify_patterns(self) -> pd.DataFrame:
        """
        Runs all pattern identification methods and populates the 'candlestick_pattern' column.
        """
        # We will implement the logic for each pattern here.
        # The order of checks might matter if a candle can be part of multiple patterns.
        # For now, we'll just call them sequentially.
        # Calculate intermediate values for pattern recognition
        self.df['body'] = abs(self.df['Close'] - self.df['Open'])
        self.df['upper_shadow'] = self.df['High'] - self.df[['Open', 'Close']].max(axis=1)
        self.df['lower_shadow'] = self.df[['Open', 'Close']].min(axis=1) - self.df['Low']
        self.df['is_bullish'] = self.df['Close'] > self.df['Open']
        self.df['is_bearish'] = self.df['Close'] < self.df['Open']

        # Simple trend detection (e.g., using a short-term SMA)
        sma_period = 10
        self.df['sma'] = self.df['Close'].rolling(window=sma_period).mean()
        self.df['is_uptrend'] = self.df['Close'] > self.df['sma']
        self.df['is_downtrend'] = self.df['Close'] < self.df['sma']

        self.identify_hammer_and_hanging_man()
        self.identify_bullish_and_bearish_engulfing()
        self.identify_piercing_line_and_dark_cloud_cover()
        self.identify_morning_star_and_evening_star()
        self.identify_three_white_soldiers_and_three_black_crows()

        # Clean up intermediate columns
        self.df.drop(columns=['body', 'upper_shadow', 'lower_shadow', 'is_bullish', 'is_bearish', 'sma', 'is_uptrend', 'is_downtrend'], inplace=True)

        return self.df

    def identify_hammer_and_hanging_man(self):
        """Identifies Hammer (bullish) and Hanging Man (bearish) patterns."""
        # Condition for Hammer/Hanging Man shape
        # Long lower shadow, small body, little to no upper shadow
        is_hammer_shape = (self.df['lower_shadow'] > self.df['body'] * 2) & \
                          (self.df['upper_shadow'] < self.df['body'] * 0.5) & \
                          (self.df['body'] > 0) # Body must exist

        # Hammer: Bullish reversal, occurs in a downtrend
        is_hammer = is_hammer_shape & self.df['is_downtrend'].shift(1)
        self.df.loc[is_hammer, 'candlestick_pattern'] = 'Hammer'

        # Hanging Man: Bearish reversal, occurs in an uptrend
        is_hanging_man = is_hammer_shape & self.df['is_uptrend'].shift(1)
        self.df.loc[is_hanging_man, 'candlestick_pattern'] = 'Hanging Man'


    def identify_bullish_and_bearish_engulfing(self):
        """Identifies Bullish and Bearish Engulfing patterns."""
        # Bullish Engulfing: Previous candle is bearish, current is bullish and engulfs the previous one.
        # Occurs in a downtrend.
        is_bullish_engulfing = (self.df['is_bearish'].shift(1)) & \
                               (self.df['is_bullish']) & \
                               (self.df['Close'] > self.df['Open'].shift(1)) & \
                               (self.df['Open'] < self.df['Close'].shift(1)) & \
                               (self.df['is_downtrend'].shift(1))
        self.df.loc[is_bullish_engulfing, 'candlestick_pattern'] = 'Bullish Engulfing'

        # Bearish Engulfing: Previous candle is bullish, current is bearish and engulfs the previous one.
        # Occurs in an uptrend.
        is_bearish_engulfing = (self.df['is_bullish'].shift(1)) & \
                              (self.df['is_bearish']) & \
                              (self.df['Open'] > self.df['Close'].shift(1)) & \
                              (self.df['Close'] < self.df['Open'].shift(1)) & \
                              (self.df['is_uptrend'].shift(1))
        self.df.loc[is_bearish_engulfing, 'candlestick_pattern'] = 'Bearish Engulfing'


    def identify_piercing_line_and_dark_cloud_cover(self):
        """Identifies Piercing Line (bullish) and Dark Cloud Cover (bearish) patterns."""
        # Piercing Line: Bullish reversal, occurs in a downtrend.
        # 1. Previous candle is bearish.
        # 2. Current candle is bullish.
        # 3. Current candle opens below previous low.
        # 4. Current candle closes above the midpoint of the previous candle's body.
        previous_body_midpoint = (self.df['Open'].shift(1) + self.df['Close'].shift(1)) / 2
        is_piercing_line = (self.df['is_downtrend'].shift(1)) & \
                           (self.df['is_bearish'].shift(1)) & \
                           (self.df['is_bullish']) & \
                           (self.df['Open'] < self.df['Low'].shift(1)) & \
                           (self.df['Close'] > previous_body_midpoint)
        self.df.loc[is_piercing_line, 'candlestick_pattern'] = 'Piercing Line'

        # Dark Cloud Cover: Bearish reversal, occurs in an uptrend.
        # 1. Previous candle is bullish.
        # 2. Current candle is bearish.
        # 3. Current candle opens above previous high.
        # 4. Current candle closes below the midpoint of the previous candle's body.
        is_dark_cloud_cover = (self.df['is_uptrend'].shift(1)) & \
                              (self.df['is_bullish'].shift(1)) & \
                              (self.df['is_bearish']) & \
                              (self.df['Open'] > self.df['High'].shift(1)) & \
                              (self.df['Close'] < previous_body_midpoint)
        self.df.loc[is_dark_cloud_cover, 'candlestick_pattern'] = 'Dark Cloud Cover'


    def identify_morning_star_and_evening_star(self):
        """Identifies Morning Star (bullish) and Evening Star (bearish) patterns."""
        # Morning Star: Bullish reversal, occurs in a downtrend.
        # 1. First candle is large and bearish.
        # 2. Second candle is small (bullish or bearish) and gaps down.
        # 3. Third candle is large and bullish, closing above the midpoint of the first candle.
        is_morning_star = (self.df['is_downtrend'].shift(2)) & \
                          (self.df['is_bearish'].shift(2)) & \
                          (self.df['body'].shift(2) > self.df['body'].rolling(10).mean().shift(2)) & \
                          (self.df['body'].shift(1) < self.df['body'].shift(2)) & \
                          (self.df['Close'].shift(1) < self.df['Close'].shift(2)) & \
                          (self.df['is_bullish']) & \
                          (self.df['Close'] > (self.df['Open'].shift(2) + self.df['Close'].shift(2)) / 2)
        self.df.loc[is_morning_star, 'candlestick_pattern'] = 'Morning Star'

        # Evening Star: Bearish reversal, occurs in an uptrend.
        # 1. First candle is large and bullish.
        # 2. Second candle is small (bullish or bearish) and gaps up.
        # 3. Third candle is large and bearish, closing below the midpoint of the first candle.
        is_evening_star = (self.df['is_uptrend'].shift(2)) & \
                          (self.df['is_bullish'].shift(2)) & \
                          (self.df['body'].shift(2) > self.df['body'].rolling(10).mean().shift(2)) & \
                          (self.df['body'].shift(1) < self.df['body'].shift(2)) & \
                          (self.df['Close'].shift(1) > self.df['Close'].shift(2)) & \
                          (self.df['is_bearish']) & \
                          (self.df['Close'] < (self.df['Open'].shift(2) + self.df['Close'].shift(2)) / 2)
        self.df.loc[is_evening_star, 'candlestick_pattern'] = 'Evening Star'


    def identify_three_white_soldiers_and_three_black_crows(self):
        """Identifies Three White Soldiers (bullish) and Three Black Crows (bearish) patterns."""
        # Three White Soldiers: Bullish reversal, occurs in a downtrend.
        # Three consecutive long bullish candles that close progressively higher.
        is_three_white_soldiers = (self.df['is_downtrend'].shift(3)) & \
                                  (self.df['is_bullish'].shift(2)) & \
                                  (self.df['is_bullish'].shift(1)) & \
                                  (self.df['is_bullish']) & \
                                  (self.df['Close'] > self.df['Close'].shift(1)) & \
                                  (self.df['Close'].shift(1) > self.df['Close'].shift(2)) & \
                                  (self.df['Open'] < self.df['Close'].shift(1)) & \
                                  (self.df['Open'] > self.df['Open'].shift(1)) & \
                                  (self.df['Open'].shift(1) < self.df['Close'].shift(2)) & \
                                  (self.df['Open'].shift(1) > self.df['Open'].shift(2))
        self.df.loc[is_three_white_soldiers, 'candlestick_pattern'] = 'Three White Soldiers'

        # Three Black Crows: Bearish reversal, occurs in an uptrend.
        # Three consecutive long bearish candles that close progressively lower.
        is_three_black_crows = (self.df['is_uptrend'].shift(3)) & \
                               (self.df['is_bearish'].shift(2)) & \
                               (self.df['is_bearish'].shift(1)) & \
                               (self.df['is_bearish']) & \
                               (self.df['Close'] < self.df['Close'].shift(1)) & \
                               (self.df['Close'].shift(1) < self.df['Close'].shift(2)) & \
                               (self.df['Open'] > self.df['Close'].shift(1)) & \
                               (self.df['Open'] < self.df['Open'].shift(1)) & \
                               (self.df['Open'].shift(1) > self.df['Close'].shift(2)) & \
                               (self.df['Open'].shift(1) < self.df['Open'].shift(2))
        self.df.loc[is_three_black_crows, 'candlestick_pattern'] = 'Three Black Crows'
