import streamlit as st
from datetime import datetime
import my_tools as mt
import streamlit.components.v1 as components

def main():
        
    # Set page config to set the page title and layout
    st.set_page_config(page_title="Stock Vision", layout="wide")

    # Title of the main page
    st.title('Stock Vision')

    # Sidebar elements
    st.sidebar.header('Input Parameters')
    ticker = st.sidebar.text_input("Ticker", value='SPY', max_chars=5)
    start_date = st.sidebar.date_input("Start Date", value=datetime(2023, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=datetime(2023, 12, 31))

    # Fetch Data button
    if st.sidebar.button('Fetch Data'):
        st.sidebar.write("Fetching data for:", ticker)
        st.sidebar.write("From:", start_date)
        st.sidebar.write("To:", end_date)
        
        df = mt.download_stock_data(ticker, start_date=start_date, end_date=end_date)        
        st.sidebar.write("Data Loaded!!!")
        message=f"Total days: {len(df)}"
        st.sidebar.write(message)


    main_view, chart_view, data_analysis = st.tabs(["Main View", "Charts", "Backtrade"])

    with main_view:
        title=f"{ticker} Data"
        st.header(title)
        st.write(df)
 
    with chart_view:
        st.header("Charts")
        fig = mt.plot_price(df, ticker)
        st.plotly_chart(fig)
        st.subheader("Data")
        df = mt.create_moving_averages(df)
        df = mt.create_sma_signals(df)
        df = mt.create_trade_signal(df, signal_column='Signal_5', sma_short='SMA_35', sma_long='SMA_50')
        st.write(df)
        
        st.write("Table of Trades (click on columns to sort)")
        trade_list = mt.create_trade_list(df, signal_column="trade_signal")
        trade_table = mt.create_trade_table(trade_list)        
        
        st.write(trade_table)
        st.write("Tabel of top performing trades")
        top_trades_df = mt.get_top_trades(trade_table, 7)
        st.write(top_trades_df)
        st.write("Table of least performing trades")
        worst_trades_df = mt.get_worst_trades(trade_table, 7)
        st.write(worst_trades_df)
  
    with data_analysis:
        st.header("Backtrade Analysis")
        st.write("This tests the following strategy: Buy on Close when price crosses up the 5 SMA and sell next day close.")
        results = mt.display_trade_summary(trade_table)
        st.write(f"Total Trades: {results["Total Trades"]}")
        st.write(f"Number of profitable trades: {results["Positive Trades"]}")
        st.write(f"Total P&L per 1 share: ${results["Accumulated Profit"]:.2f}")
        st.subheader("Top 5 Trades")        
        for i in range(5):
            st.write(f"Trade {i+1}")            
            st.write(f"Date: {results["Top 5 Trades"][i]["Date"]}")
            st.write(f"Buy Price: $ {results["Top 5 Trades"][i]["buy_price"]:.2f}")
            st.write(f"Sell Price: $ {results["Top 5 Trades"][i]["sell_price"]:.2f}")
            st.write(f"Trade P&L: ${results["Top 5 Trades"][i]["profit"]:.2f}")
            st.write("------------")

if __name__ == "__main__":
    main()