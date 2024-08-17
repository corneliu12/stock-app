import streamlit as st
import datetime
import my_tools as mt
import yfinance as yf  # Ensure yfinance is imported

# Set the page configuration to wide mode
st.set_page_config(layout="wide")

# Ensure session state to store fetched data, company name, symbol, and selected SMA windows
if "data" not in st.session_state:
    st.session_state["data"] = None

if "company_name" not in st.session_state:
    st.session_state["company_name"] = None

if "ticker" not in st.session_state:
    st.session_state["ticker"] = "AAPL"

if "start_date" not in st.session_state:
    st.session_state["start_date"] = datetime.date(2023, 1, 1)

if "end_date" not in st.session_state:
    st.session_state["end_date"] = datetime.date.today()

if "selected_windows" not in st.session_state:
    st.session_state["selected_windows"] = []

if "created_smas" not in st.session_state:
    st.session_state["created_smas"] = []

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Data",  "SMAs", "Charts", "Trading Strategy"])

# User instructions in the sidebar
st.sidebar.info("Select a view from the sidebar. Start by fetching stock data, then calculate SMAs or view charts.")

# Data View
if page == "Data":
    st.title("Stock Data")

    # Create columns for user input fields
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        ticker = st.text_input("Ticker Symbol", value=st.session_state["ticker"])
    with col2:
        start_date = st.date_input("Start Date", value=st.session_state["start_date"])
    with col3:
        end_date = st.date_input("End Date", value=st.session_state["end_date"])

    # Update session state when inputs change
    st.session_state["ticker"] = ticker
    st.session_state["start_date"] = start_date
    st.session_state["end_date"] = end_date
    
    # Fetch data button with error handling
    if st.button("Fetch Data"):
        try:
            # Fetch stock data
            st.session_state["data"] = mt.download_stock_data(ticker, start_date, end_date)
            
            # Fetch company information
            ticker_info = yf.Ticker(ticker)
            st.session_state["company_name"] = ticker_info.info.get('shortName', 'N/A')
            st.session_state["symbol"] = ticker_info.info.get('symbol', 'N/A')
            
            # Display the fetched data and company information
            text = f"### Company Name: {st.session_state['company_name']} ({ticker.upper()})"
            st.markdown(text)
            st.write(f"Showing data for {ticker.upper()} from {start_date} to {end_date}:")
            st.dataframe(st.session_state["data"])
        except Exception as e:
            st.error(f"Failed to fetch data for {ticker}. Error: {e}")
    
    # Display the stored data if it already exists
    elif st.session_state["data"] is not None:
        text = f"### Company Name: {st.session_state['company_name']} ({ticker.upper()})"
        st.markdown(text)
        st.write(f"Showing data for {st.session_state['ticker'].upper()} from {st.session_state['start_date']} to {st.session_state['end_date']}:")
        st.dataframe(st.session_state["data"])

# SMA View
elif page == "SMAs":
    st.title("SMAs")

    if st.session_state["data"] is not None:
        st.subheader("Select SMA Windows")

        # Function to handle SMA selection
        def get_sma_selection():
            sma_options = {
                "SMA 2": 2, "SMA 3": 3, "SMA 5": 5, "SMA 7": 7, "SMA 10": 10,
                "SMA 14": 14, "SMA 20": 20, "SMA 35": 35, "SMA 50": 50, "SMA 100": 100
            }
            selected_windows = []
            for key, value in sma_options.items():
                if st.checkbox(key, value=value in st.session_state["selected_windows"]):
                    selected_windows.append(value)
            return selected_windows

        # Update the selected windows list
        st.session_state["selected_windows"] = get_sma_selection()
        
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
    chart_title = f"Chart for {st.session_state['company_name']} ({st.session_state['ticker'].upper()})"
    st.title(chart_title)

    if st.session_state.get("data") is not None and "ticker" in st.session_state and "created_smas" in st.session_state:
        # Create two columns
        col1, col2 = st.columns(2)

        # Set default indexes for SMAs
        if st.session_state.get("created_smas"):
            ma1_index = 0
            ma2_index = 1 if len(st.session_state["created_smas"]) > 1 else 0

            # Place the selectboxes in the columns
            with col1:
                ma1 = st.selectbox("Select first SMA for chart (MA1)", st.session_state["created_smas"], index=ma1_index)

            with col2:
                ma2 = st.selectbox("Select second SMA for chart (MA2)", st.session_state["created_smas"], index=ma2_index)

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

    # Assuming SMAs have been calculated and stored in st.session_state['created_smas']
    st.session_state['created_smas'] = st.session_state.get('created_smas', ['SMA5', 'SMA10', 'SMA20'])

    # Ensure all items in created_smas are strings
    created_smas = [str(sma) for sma in st.session_state['created_smas']]

    # Create a mapping of SMA values to descriptive labels
    sma_labels = {sma: f"{sma.replace('SMA', '')} Day SMA" for sma in created_smas}
    options = ["Close"] + list(sma_labels.values())

    # Set up the layout with a single main column
    col1 = st.columns(1)[0]

    # Entry Strategy in the main column
    with col1:
        st.header("Entry Strategy")

        # Create a single row with three columns for the inputs
        entry_col1, entry_col2, entry_col3 = st.columns([1, 1, 1])

        with entry_col1:
            entry_sma1_label = st.selectbox("SMA", options, key='entry_sma1', help="Select the first SMA or Close for the entry condition.")
            entry_sma1 = "Close" if entry_sma1_label == "Close" else [k for k, v in sma_labels.items() if v == entry_sma1_label][0]
        with entry_col2:
            entry_condition = st.selectbox("Condition", ["greater than", "less than"], key='entry_condition', help="Select the condition for the entry strategy.")
        with entry_col3:
            entry_sma2_label = st.selectbox("Compare to", options, key='entry_sma2', help="Select the second SMA or Close to compare with the first one.")
            entry_sma2 = "Close" if entry_sma2_label == "Close" else [k for k, v in sma_labels.items() if v == entry_sma2_label][0]

        # Display the chosen Entry Strategy
        st.write(f"Entry Strategy: Enter when {entry_sma1_label} is {entry_condition} {entry_sma2_label}.")

    # Exit Strategy directly below the Entry Strategy in the same column
    with col1:
        st.header("Exit Strategy")

        # Create a single row with three columns for the inputs
        exit_col1, exit_col2, exit_col3 = st.columns([1, 1, 1])

        with exit_col1:
            exit_sma1_label = st.selectbox("SMA", options, key='exit_sma1', help="Select the first SMA or Close for the exit condition.")
            exit_sma1 = "Close" if exit_sma1_label == "Close" else [k for k, v in sma_labels.items() if v == exit_sma1_label][0]
        with exit_col2:
            exit_condition = st.selectbox("Condition", ["greater than", "less than"], key='exit_condition', help="Select the condition for the exit strategy.")
        with exit_col3:
            exit_sma2_label = st.selectbox("Compare to", options, key='exit_sma2', help="Select the second SMA or Close to compare with the first one.")
            exit_sma2 = "Close" if exit_sma2_label == "Close" else [k for k, v in sma_labels.items() if v == exit_sma2_label][0]

        # Display the chosen Exit Strategy
        st.write(f"Exit Strategy: Exit when {exit_sma1_label} is {exit_condition} {exit_sma2_label}.")
