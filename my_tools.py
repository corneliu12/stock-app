import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def company_info(ticker):
    company = yf.Ticker(ticker)
    return company.info


def download_stock_data(ticker, start_date, end_date=None):
    """
    Downloads historical stock data from Yahoo Finance.

    :param ticker: str, stock ticker symbol
    :param start_date: str, start date in the format 'YYYY-MM-DD'
    :param end_date: str, end date in the format 'YYYY-MM-DD' (default is today's date)
    :return: pd.DataFrame, DataFrame containing the historical stock data
    """
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    
    return stock_data

def plot_price(dataframe, ticker="", column='Adj Close'):
    """
    Plots the specified column over time from a DataFrame using Plotly.

    :param dataframe: pd.DataFrame, DataFrame with a DateTime index
    :param ticker: str, stock ticker symbol for the title
    :param column: str, the column to plot (default is 'Adj Close')
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=dataframe.index, y=dataframe[column], mode='lines', name=column))

    fig.update_layout(
        width=900,
        height=900,
        title=f'{ticker.upper()} {column} Over Time',
        xaxis_title='Date',
        yaxis_title=column,
        xaxis=dict(
            tickformat='%Y-%m-%d',
            tickmode='auto',
            tickangle=45
        ),
        yaxis=dict(
            side='right'
        ),
        template='plotly_dark'
    )

    return fig

def create_moving_averages(dataframe, column='Close', windows=[2, 3, 5, 7, 10, 20, 35, 50]):
    """
    Adds moving averages to the DataFrame for the specified window lengths.

    :param dataframe: pd.DataFrame, the DataFrame to add moving averages to
    :param column: str, the column to calculate moving averages on (default is 'Adj Close')
    :param windows: list of int, the window lengths for the moving averages (default is [10, 20, 50, 100, 200])
    :return: pd.DataFrame, the DataFrame with added moving average columns
    """
    if not (1 <= len(windows) <= 10):
        raise ValueError("Number of windows must be between 1 and 5")
    
    for window in windows:
        dataframe[f'SMA_{window}'] = dataframe[column].rolling(window=window).mean()
    
    return dataframe

def create_sma_signals(dataframe, column='Close', windows=[2, 3, 5, 7, 10, 20, 35, 50]):
    """
    Adds signal columns to the DataFrame to indicate when the specified column (price) crosses above the moving averages.

    :param dataframe: pd.DataFrame, the DataFrame to add signal columns to
    :param column: str, the column to check against the moving averages (default is 'Adj Close')
    :param windows: list of int, the window lengths for the moving averages (default is [10, 20, 50, 100, 200])
    :return: pd.DataFrame, the DataFrame with added signal columns
    """
    for window in windows:
        sma_column = f'SMA_{window}'
        signal_column = f'Signal_{window}'

        if sma_column not in dataframe.columns:
            raise ValueError(f"Moving average column '{sma_column}' not found in DataFrame. Please run create_moving_averages first.")

        # Create the signal column
        dataframe[signal_column] = (dataframe[column] > dataframe[sma_column]) & (dataframe[column].shift(1) <= dataframe[sma_column].shift(1))

    return dataframe

def create_trade_signal(dataframe, signal_column='Signal_5', sma_short='SMA_5', sma_long='SMA_10'):
    """
    Creates a column 'trade_signal' in the DataFrame which is True if signal_column is True and sma_short is greater than sma_long.

    :param dataframe: pd.DataFrame, the DataFrame to modify
    :param signal_column: str, the column indicating signal points
    :param sma_short: str, the column for the short-term SMA
    :param sma_long: str, the column for the long-term SMA
    :return: pd.DataFrame, the modified DataFrame with the 'trade_signal' column
    """
    dataframe['trade_signal'] = (dataframe[signal_column]) & (dataframe[sma_short] > dataframe[sma_long])
    return dataframe


def add_next_day_column(dataframe, column):
    """
    Adds a column to the DataFrame for the next day's value of the specified column.

    :param dataframe: pd.DataFrame, the DataFrame to add the new column to
    :param column: str, the column to calculate the next day's value
    :return: pd.DataFrame, the DataFrame with the added column
    """
    next_day_column = f'{column}_Next_Day'
    
    # Add next day's value column
    dataframe[next_day_column] = dataframe[column].shift(-1)
    
    return dataframe

def create_trade_list(dataframe, signal_column, buy_price_column='Adj Close', open_price_column='Open', order='default'):
    """
    Creates a list of dictionaries with the following keys and values only when the signal is true:
    - 'Date': Date value from the DataFrame
    - 'buy_price': Value from the specified buy price column
    - 'sell_price': Value from the next day's specified buy price column
    - 'profit': Difference between the next day's sell price and the buy price
    - 'candle_type': 'red' if Adj Close is less than Open, otherwise 'green'

    :param dataframe: pd.DataFrame, the DataFrame to create the list of dictionaries from
    :param signal_column: str, the column indicating signal points
    :param buy_price_column: str, the column to use as the buy price
    :param open_price_column: str, the column to use as the open price
    :param order: str, the order in which to return the list ('default', 'profit_desc', 'profit_asc')
    :return: list of dict, list containing dictionaries with the specified keys and values when the signal is true
    """
    # Ensure the next day 'Adj Close' column exists
    next_day_column = f'{buy_price_column}_Next_Day'
    if next_day_column not in dataframe.columns:
        dataframe[next_day_column] = dataframe[buy_price_column].shift(-1)
    
    # Calculate profit
    profit_column = 'profit'
    dataframe[profit_column] = dataframe[next_day_column] - dataframe[buy_price_column]
    
    # Determine candle type
    candle_type_column = 'candle_type'
    dataframe[candle_type_column] = dataframe.apply(lambda row: 'red' if row[buy_price_column] < row[open_price_column] else 'green', axis=1)
    
    # Filter the DataFrame where the signal is true
    signal_df = dataframe[dataframe[signal_column]]
    
    # Create the list of dictionaries
    trade_list = [
        {
            'Date': date,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'profit': profit,
            'candle_type': candle_type
        }
        for date, buy_price, sell_price, profit, candle_type in zip(signal_df.index, signal_df[buy_price_column], signal_df[next_day_column], signal_df[profit_column], signal_df[candle_type_column])
    ]
    
    # Sort the list based on the order parameter
    if order == 'profit_desc':
        trade_list = sorted(trade_list, key=lambda x: x['profit'], reverse=True)
    elif order == 'profit_asc':
        trade_list = sorted(trade_list, key=lambda x: x['profit'])
    
    return trade_list



def create_trade_table(trade_list):
    """
    Converts the trade list into a pandas DataFrame to create a table.

    :param trade_list: list of dict, list containing trade dictionaries
    :return: pd.DataFrame, DataFrame representing the trade table
    """
    trade_table = pd.DataFrame(trade_list)
    trade_table['accumulated_profit'] = trade_table['profit'].cumsum()
    return trade_table



def get_top_trades(trade_table, num_trades):
    """
    Returns a DataFrame containing the top trades with the best profit in order from greatest to least.

    :param trade_table: pd.DataFrame, DataFrame representing the trade table
    :param num_trades: int, the number of top trades to return
    :return: pd.DataFrame, DataFrame containing the top trades ordered by profit
    """
    # Drop the 'accumulated_profit' column if it exists
    if 'accumulated_profit' in trade_table.columns:
        trade_table = trade_table.drop(columns=['accumulated_profit'])
    
    top_trades = trade_table.nlargest(num_trades, 'profit').copy()
    top_trades = top_trades.sort_values(by='profit', ascending=False)
    return top_trades

def get_worst_trades(trade_table, num_trades):
    """
    Returns a DataFrame containing the least profitable trades in order from worst to best.

    :param trade_table: pd.DataFrame, DataFrame representing the trade table
    :param num_trades: int, the number of worst trades to return
    :return: pd.DataFrame, DataFrame containing the least profitable trades ordered by profit
    """
    # Drop the 'accumulated_profit' column if it exists
    if 'accumulated_profit' in trade_table.columns:
        trade_table = trade_table.drop(columns=['accumulated_profit'])
    
    worst_trades = trade_table.nsmallest(num_trades, 'profit').copy()
    worst_trades = worst_trades.sort_values(by='profit', ascending=True)
    return worst_trades

def display_trade_summary(trade_table):
    """
    Returns a dictionary containing the summary of the trades including the accumulated profit,
    the number of positive trades, and the top 5 largest and bottom 5 smallest profits.

    :param trade_table: pd.DataFrame, DataFrame representing the trade table
    :return: dict, dictionary containing the summary data
    """
    summary = {}
    
    accumulated_profit = trade_table['profit'].sum()
    positive_trades = (trade_table['profit'] > 0).sum()
    total_trades = len(trade_table)
    
    top_5_profits = trade_table.nlargest(5, 'profit')
    bottom_5_profits = trade_table.nsmallest(5, 'profit')

    summary['Total Trades'] = total_trades
    summary['Positive Trades'] = positive_trades
    summary['Accumulated Profit'] = accumulated_profit
    summary['Top 5 Trades'] = top_5_profits.to_dict(orient='records')
    summary['Bottom 5 Trades'] = bottom_5_profits.to_dict(orient='records')
    
    return summary

import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# The candlestick plot function
def get_candlestick_plot(
        df: pd.DataFrame,
        ma1: int,
        ma2: int,
        ticker: str,
        template = 'plotly',
        width=1200  # Specify the desired width here
    ):
    '''
    Create the candlestick chart with two moving avgs + a plot of the volume
    Parameters
    ----------
    df : pd.DataFrame
        The price dataframe
    ma1 : int
        The length of the first moving average (days)
    ma2 : int
        The length of the second moving average (days)
    ticker : str
        The ticker we are plotting (for the title).
    '''
    
    fig = make_subplots(
        rows = 2,
        cols = 1,
        shared_xaxes = True,
        vertical_spacing = 0.1,
        subplot_titles = (f'{ticker} Stock Price', 'Volume Chart'),
        row_heights=[0.7, 0.3]
    )
    
    # Update layout
    fig.update_layout(height=900, template=template)

    fig.add_trace(
        go.Candlestick(
            x = df.index,
            open = df['Open'], 
            high = df['High'],
            low = df['Low'],
            close = df['Close'],
            name = 'Candlestick chart'
        ),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
        go.Scatter(x = df.index, y = df[f'SMA_{ma1}'], mode='lines', name = f'{ma1} SMA'),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
        go.Scatter(x = df.index, y = df[f'SMA_{ma2}'], mode='lines', name = f'{ma2} SMA'),
        row = 1,
        col = 1,
    )
    
    fig.add_trace(
        go.Bar(x = df.index, y = df['Volume'], name = 'Volume'),
        row = 2,
        col = 1,
    )

    # Update axis titles
    fig.update_xaxes(title_text='Date', row=2, col=1)
    fig.update_yaxes(title_text='Price', row=1, col=1)
    fig.update_yaxes(title_text='Volume', row=2, col=1)
    
    fig.update_xaxes(
        rangebreaks = [{'bounds': ['sat', 'mon']}],
        rangeslider_visible = False,
    )
    
    return fig

def generate_signal(df, sma1, condition, sma2):
    """
    Generates a signal column based on the condition between two SMAs or an SMA and the Close price.
    
    Args:
    - df: DataFrame containing the stock data and SMAs.
    - sma1: The first SMA (or 'Close') to compare.
    - condition: The condition ('greater than' or 'less than').
    - sma2: The second SMA (or 'Close') to compare against.
    
    Returns:
    - A Series with True/False values indicating where the condition is met.
    """
    series1 = df[sma1] if sma1 != 'Close' else df['Close']
    series2 = df[sma2] if sma2 != 'Close' else df['Close']
    
    if condition == 'greater than':
        return series1 > series2
    elif condition == 'less than':
        return series1 < series2
    else:
        raise ValueError("Condition must be either 'greater than' or 'less than'.")


