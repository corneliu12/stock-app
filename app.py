import streamlit as st
import pandas as pd
import datetime
import my_tools as mt

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Ensure session state to store fetched data and selected SMA windows
if "data" not in st.session_state:
    st.session_state["data"] = None

if "selected_windows" not in st.session_state:
    st.session_state["selected_windows"] = []

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Data",  "SMAs", "Charts", "Trading Strategy"])

# Data View
if page == "Data":
    st.title("Data")

    # Create columns for user input fields
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        ticker = st.text_input("Ticker Symbol", value="AAPL")
        st.session_state["ticker"] = ticker  # Store ticker in session state
    with col2:
        start_date = st.date_input("Start Date", value=datetime.date(2023, 1, 1))
    with col3:
        end_date = st.date_input("End Date", value=datetime.date.today())

    # Fetch data button
    if st.button("Fetch Data"):
        st.session_state["data"] = mt.download_stock_data(ticker, start_date, end_date)
        st.write(f"Showing data for {ticker} from {start_date} to {end_date}:")
        st.dataframe(st.session_state["data"])

# SMA View
elif page == "SMAs":
    st.title("SMAs")

    if st.session_state["data"] is not None:
        st.subheader("Select SMA Windows")

        # Create two rows with 5 checkboxes each
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            sma_2 = st.checkbox("SMA 2", value=2 in st.session_state["selected_windows"])
            sma_3 = st.checkbox("SMA 3", value=3 in st.session_state["selected_windows"])
        with col2:
            sma_5 = st.checkbox("SMA 5", value=5 in st.session_state["selected_windows"])
            sma_7 = st.checkbox("SMA 7", value=7 in st.session_state["selected_windows"])
        with col3:
            sma_10 = st.checkbox("SMA 10", value=10 in st.session_state["selected_windows"])
            sma_14 = st.checkbox("SMA 14", value=14 in st.session_state["selected_windows"])
        with col4:
            sma_20 = st.checkbox("SMA 20", value=20 in st.session_state["selected_windows"])
            sma_35 = st.checkbox("SMA 35", value=35 in st.session_state["selected_windows"])
        with col5:
            sma_50 = st.checkbox("SMA 50", value=50 in st.session_state["selected_windows"])
            sma_100 = st.checkbox("SMA 100", value=100 in st.session_state["selected_windows"])

        # Update the selected windows list
        st.session_state["selected_windows"] = []
        if sma_2: st.session_state["selected_windows"].append(2)
        if sma_3: st.session_state["selected_windows"].append(3)
        if sma_5: st.session_state["selected_windows"].append(5)
        if sma_7: st.session_state["selected_windows"].append(7)
        if sma_10: st.session_state["selected_windows"].append(10)
        if sma_14: st.session_state["selected_windows"].append(14)
        if sma_20: st.session_state["selected_windows"].append(20)
        if sma_35: st.session_state["selected_windows"].append(35)
        if sma_50: st.session_state["selected_windows"].append(50)
        if sma_100: st.session_state["selected_windows"].append(100)
        
        # Create SMA button
        if st.button("Create SMA"):
            if st.session_state["selected_windows"]:
                sma_df = mt.create_moving_averages(st.session_state["data"], windows=st.session_state["selected_windows"])
                st.session_state["created_smas"] = st.session_state["selected_windows"]
                st.write("SMAs created for the following windows:", st.session_state["selected_windows"])
                st.dataframe(sma_df)
            else:
                st.write("No SMA windows selected.")
    else:
        st.write("Please fetch data in the 'Data' view first.")

# Charts View
elif page == "Charts":
    st.title("Charts")

    if st.session_state.get("data") is not None and "ticker" in st.session_state and "created_smas" in st.session_state:
        # User selects from created SMAs
        ma1 = st.selectbox("Select first SMA for chart (MA1)", st.session_state["created_smas"])
        ma2 = st.selectbox("Select second SMA for chart (MA2)", st.session_state["created_smas"])



        # Create the candlestick plot
        fig = mt.get_candlestick_plot(
            df=st.session_state["data"],
            ma1=ma1,
            ma2=ma2,
            ticker=st.session_state["ticker"] 
        )

        # Display the chart
        st.plotly_chart(fig)
    else:
        st.write("Please fetch data in the 'Data' view first.")

# Trading Strategy View
elif page == "Trading Strategy":
    st.title("Trading Strategy")
    st.write("Define your trading strategy here.")

    # Example of a simple strategy explanation
    st.write("**Strategy:** Buy when the Close is above SMA5. Sell when the Close drops below SMA10 or the entry day’s low.")
    
    # Additional strategy logic or visualization can go here
