import streamlit as st
import pandas as pd
import yfinance as yf
import datetime as dt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import MonthEnd
import matplotlib.pyplot as plt
from matplotlib import style

style.use('ggplot')

# Ticker Lists and Sidebar---------------------------------------------------------------------------
tickerSensex = pd.read_csv('./data/BSE_Company_List.csv')
tickerSensex = tickerSensex.Symbol.to_list()
tickerSP = pd.read_csv('./data/SP_Company_List.csv')
tickerSP = tickerSP.Symbol.to_list()
tickerCrypto = pd.read_csv('./data/Crypto_List.csv')
tickerCrypto = tickerCrypto.Symbol.to_list()
tickerFTSE = pd.read_csv('./data/FTSE_company_list.csv')
tickerFTSE = tickerFTSE.Symbol.to_list()

st.sidebar.header('BSE Ticker')
ticker_selection = st.sidebar.multiselect("Entity Name", options = tickerSensex)

st.sidebar.header('S&P Ticker')
ticker_selection_sp = st.sidebar.multiselect("Entity Name", options = tickerSP)

st.sidebar.header('FTSE Ticker')
ticker_selection_ftse = st.sidebar.multiselect("Entity Name", options = tickerFTSE)

st.sidebar.header('Crypto Ticker')
ticker_selection_crypto = st.sidebar.multiselect("Entity Name", options = tickerCrypto)

ticker_selection = ticker_selection + ticker_selection_sp + ticker_selection_crypto + ticker_selection_ftse

