from numpy.random.mtrand import sample
from pandas.core.dtypes.missing import notnull
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
from forex_python.converter import CurrencyRates
from fitter import Fitter, get_common_distributions, get_distributions
from scipy.stats import norm, t, nct, beta

st.set_page_config(
     page_title="Portfolio Analysis",
     # page_icon="🧊",
     layout="wide",
     initial_sidebar_state="expanded",
    #  menu_items={
    #      'Get Help': 'https://www.extremelycoolapp.com/help',
    #      'Report a bug': "https://www.extremelycoolapp.com/bug",
    #      'About': "# This is a header. This is an *extremely* cool app!"
    #  }
 )


style.use('ggplot')


page = st.sidebar.selectbox(label = "Choose Page", options = ['Page 1', 'Page 2', 'Page 3'])


# Invoking CurrecnyRates object------------------------------------------------------------------------
c = CurrencyRates()

# No of Simulations ------------------------------------------------------------------------------------------
N = 6000

# Risk-free rate -------------------------------------------------------------------------------------------- 
RF = 0.02

# Creating a Date Range-----------------------------------------------------------------------
date = st.sidebar.date_input(label = 'Year', value = dt.datetime(2021, 1, 6))

# Currency choice---------------------------------------------------------------------------
currency_opt = st.sidebar.selectbox('Currency Type', options = ['INR', 'USD', 'GBP'])

# Choice of PCT or Log difference of prices---Ln 95------------------------------------------------------------
diff_choice = st.sidebar.selectbox('Select Price Change Metric' , ['Log Change', 'Percent Change'])


# Ticker Lists and Sidebar---------------------------------------------------------------------------
tickerBSE = pd.read_csv('./data/BSE_Company_List.csv')
tickerBSE = tickerBSE.Symbol.to_list()
tickerSP = pd.read_csv('./data/SP_Company_List.csv')
tickerSP = tickerSP.Symbol.to_list()
tickerCrypto = pd.read_csv('./data/Crypto_List.csv')
tickerCrypto = tickerCrypto.Symbol.to_list()
tickerFTSE = pd.read_csv('./data/FTSE_company_list.csv')
tickerFTSE = tickerFTSE.Symbol.to_list()

st.sidebar.header('BSE Ticker')
ticker_selection_bse = st.sidebar.multiselect("Entity Name", options = tickerBSE)

st.sidebar.header('S&P Ticker')
ticker_selection_sp = st.sidebar.multiselect("Entity Name", options = tickerSP)

st.sidebar.header('FTSE Ticker')
ticker_selection_ftse = st.sidebar.multiselect("Entity Name", options = tickerFTSE)

st.sidebar.header('Crypto Ticker')
ticker_selection_crypto = st.sidebar.multiselect("Entity Name", options = tickerCrypto)

ticker_selection = ticker_selection_bse + ticker_selection_sp + ticker_selection_crypto + ticker_selection_ftse



# Downloading Data from Yahooo Finance---------------------------------------------------------------------------
@st.cache
def market_data(tickers, dt):
    data = []
    tmp_data = yf.download(tickers, start = dt)
    tmp_data = tmp_data['Adj Close']
    tmp_data = tmp_data.dropna()
    return(tmp_data)


df_1 = market_data(ticker_selection, date)

if diff_choice == 'Percent Change':
    df_returns_pct = df_1.pct_change()
    df_returns_pct = df_returns_pct.dropna()
    df_returns_pct = df_returns_pct.replace(np.Inf, -1)
    df_returns = df_returns_pct

# if st.sidebar.checkbox('Log Change'):
elif diff_choice == 'Log Change':    
    def log_change(data):
        ret = np.diff(np.log(data))
        return ret
    df_returns = pd.DataFrame()
    df_returns = df_1.apply(log_change)
    df_returns.index = df_1.index[1:]

# Performig the currency converison --------------------------------------------------------------------------
@st.cache
def currency_conversion(currency = 'INR'):
    df_sp_crypto = df_1[ticker_selection_sp + ticker_selection_crypto]
    df_ftse = df_1[ticker_selection_ftse]
    df_bse = df_1[ticker_selection_bse]

    if currency == 'INR':
        df_sp_crypto = c.convert('USD', currency, df_sp_crypto)
        df_ftse = c.convert('GBP', currency, df_ftse)

    elif currency  == 'USD':
        df_bse = c.convert('INR',currency, df_bse)
        df_ftse = c.convert('GBP', currency, df_ftse)

    elif currency == 'GBP':
        df_bse = c.convert('INR', currency, df_bse)
        df_sp_crypto = c.convert('USD', currency, df_sp_crypto)

    df_tmp_all_ticker = pd.concat( [df_sp_crypto, df_ftse, df_bse] , axis = 1)

    return(df_tmp_all_ticker)

df_1 = currency_conversion(currency_opt)


if page == 'Page 1':

    # Initiating the 3 tabs for Page 1---------------------------------------------------------------------------
    tab1, tab2, tab3 = st.columns(3)

    # Displaying Ticker Selection Data with an Expander----------------------------------------------------------
    stick_data_expander = st.expander('Display Data')
    stick_data_expander.write(df_1)

 
    # Selecting either Regualar percent change or Log change-------------------------------------------------------
    # ret1,ret2 = st.columns(2)
    # if st.sidebar.checkbox('Percentage Change', value = True):
    # if diff_choice == 'Percentage Change':
    #     df_returns_pct = df_1.pct_change()
    #     df_returns_pct = df_returns_pct.dropna()
    #     df_returns_pct = df_returns_pct.replace(np.Inf, -1)
    #     df_returns = df_returns_pct

    # # if st.sidebar.checkbox('Log Change'):
    # if diff_choice == 'Log Change':    
    #     def log_change(data):
    #         ret = np.diff(np.log(data))
    #         return ret
    #     df_returns = pd.DataFrame()
    #     df_returns = df_1.apply(log_change)
    #     df_returns.index = df_1.index[1:]



    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    # Page 1 Tab 1 - Visualization ######################################################################################
    if tab1.button('Simple Visualization'):
        # Visualization
        ## Line Chart of Adj. Close Prices
        plt.plot(df_1)
        plt.legend(ticker_selection)
        st.subheader('Line Chart')
        fig_line = go.Figure()
        for ticker in ticker_selection:
            fig_line.add_trace(go.Scatter(x = df_1.index, y = df_1[ticker], name = ticker))
        
        st.plotly_chart(fig_line)
        

        ## Histograms and PCT change line chart
        st.subheader('PCT change Line Chart')

        fig_pct = go.Figure()
        for ticker in ticker_selection:
            fig_pct.add_trace(go.Scatter(x = df_1.index, y = df_returns[ticker], name = ticker))
        
        st.plotly_chart(fig_pct)
     


        hist_data = (df_returns.to_numpy()).T
        group_labels = df_returns.columns

        ### Preprocessing and removing error values that might throwoff the histogram
        st.subheader("Histogram Plots")

        # Plotly Plot
        fig = go.Figure()
        for ticker in ticker_selection:
            fig.add_trace(go.Histogram(x = df_returns[ticker], name = ticker))
            fig.update_layout(barmode = 'overlay')
            fig.update_traces(opacity = 0.6)
      
        st.plotly_chart(fig)

    #####################################################################################################################



    # Custom Portfolio Sidebar Input-------------------------------------------------------------------------------------
    wts_custom = []
    lock_toggle_list = []
    lock_toggle_ticker_list = []
    wts_locked = []
    custom_toggle = 0
    if st.sidebar.checkbox('Custom Portfolio'):
        custom_toggle = 1
        for ticker in ticker_selection:
            tmp_no_input = st.sidebar.number_input(ticker, min_value = 0.0, max_value = 1.0)
            label_name = f'Lock {ticker}'
            if st.sidebar.checkbox(label = label_name):
                lock_toggle = 1
                lock_toggle_ticker_list.append(ticker)
                wts_locked.append(tmp_no_input)
            else: 
                lock_toggle = 0
            wts_custom.append(tmp_no_input)
            lock_toggle_list.append(lock_toggle)


        # Rearranging the ticker names based onwhen the lock toggle is activated-----------------------------------------
        item_list = [e for e in ticker_selection if e not in lock_toggle_ticker_list]




        # Cutom Portfolio Metrics----------------------------------------------------------------------------------------
        df_returns_mean = df_returns.mean() * 252
        annualized_returns_custom = np.sum(df_returns_mean * wts_custom)
        matrix_covariance_custom = df_returns.cov() * 252
        portfolio_variance_custom = np.dot(wts_custom, np.dot(matrix_covariance_custom, wts_custom))
        portfolio_std_custom = np.sqrt(portfolio_variance_custom)
        sharpe_custom = (annualized_returns_custom - RF) / portfolio_std_custom
        custom_portfolio_metrics = [annualized_returns_custom, portfolio_std_custom, sharpe_custom]

        # Custom Portfolio Metrics Output on main page Tab 2 -------------------------------------------------------------
        st.header('Custom Portfolio Metrics')  
        col1, col2, col3 = st.columns(3)
        col1.metric(label = 'Annualized Returns', value = np.round(custom_portfolio_metrics[0], 2))
        col2.metric(label = 'Annualized Risk',value = np.round(custom_portfolio_metrics[1], 2))
        col3.metric(label = 'Sharpe Ratio', value = np.round(custom_portfolio_metrics[2], 2))


    # Defining Function to construct weights for simulation for lock and default states ---------------------------------
    def weights_simulation(lock = 0):
        if lock == 0:
            weights_tmp = np.random.random(len(ticker_selection))
            weights_tmp = np.round(weights_tmp / np.sum(weights_tmp), 4)

        elif lock == 1:
            weights_tmp = np.random.random(len(ticker_selection) - len(wts_locked))
            weights_tmp = np.round(weights_tmp / np.sum(weights_tmp), 4)
            weights_tmp = weights_tmp * (1 - np.sum(wts_locked)) 
            weights_tmp = np.hstack([weights_tmp, wts_locked])

        return weights_tmp




    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    # Page 1 Tab 2 -  ###################################################################################################
    if tab2.button('Portfolio Optimization'):

        if len(lock_toggle_ticker_list) == 0:
            lock_toggle = 0
        else:
            lock_toggle = 1



        st.header('Efficient Frontier Analysis')

        # Defining function to plot the Efficient Frontier and Portfolio Metrics Dataframes-------

        def efficient_frontier(no_portfolios = 100, RF = 0.05, custom = 0, lock = 0):
            portfolio_returns = []
            portfolio_risk = []
            weights = []
            sharpe_ratio = []
            portfolio_weights = []
            df_returns_mean = df_returns.mean() * 252
            matrix_covariance = df_returns.cov() * 252
            
            i = 0
            for i in range(no_portfolios):
            # Generate Random Weights---------------------------------------------------------
                weights = weights_simulation(lock)
                portfolio_weights.append(weights)


                # Annualized Returns--------------------------------------------------------------
                annualized_returns = np.sum(df_returns_mean * weights) # Already annualized
                portfolio_returns.append(annualized_returns)

                # Covariance Matrix & Portfolio Risk Calc-----------------------------------------
                portfolio_variance = np.dot(weights.T, np.dot(matrix_covariance, weights))
                portfolio_std = np.sqrt(portfolio_variance)
                portfolio_risk.append(portfolio_std)

                # Sharpe Ratio---------------------------------------------------------------------
                sharpe = (annualized_returns - RF) / portfolio_std
                sharpe_ratio.append(sharpe)


            # Dataframe from Analysing all the simulated portfolios ----------------------------------------------
            df_metrics = pd.DataFrame([np.array(portfolio_returns),
                                    np.array(portfolio_risk),
                                    np.array(sharpe_ratio),
                                    str(np.array(portfolio_weights))], index = ['Returns', 'Risk', 'Sharpe_ratio', 'Weights'])

            df_metrics = df_metrics.T
            

            # Finfing the min risk portfolio
            min_risk = df_metrics.iloc[df_metrics['Risk'].astype(float).idxmin()]
            wt_min  = portfolio_weights[df_metrics['Risk'].astype(float).idxmin()]
            # Finding the max return portfolio    
            max_return = df_metrics.iloc[df_metrics['Returns'].astype(float).idxmax()]
            wt_max  = portfolio_weights[df_metrics['Returns'].astype(float).idxmin()]
            # Finding the portfolio with max Sharpe Ratio    
            max_sharpe = df_metrics.iloc[df_metrics['Sharpe_ratio'].astype(float).idxmax()]
            wt_sharpe  = portfolio_weights[df_metrics['Sharpe_ratio'].astype(float).idxmax()]

            # Isolating the weights from the above mentioned 3 portfolios
            weights = pd.DataFrame([wt_min, wt_max, wt_sharpe], index = ['Min Risk', 'Max Return', 'Max Sharpe Ratio'], columns = ticker_selection)


        # Plotting the Efficient Frontier -------------------------------------------------------------------------
            df_metrics['Sharpe Ratio'] = df_metrics['Sharpe_ratio'].to_numpy(dtype = float)
        
            fig = go.Figure()
            c = fig.add_trace(go.Scatter(x = df_metrics['Risk'], y = df_metrics['Returns'], mode = 'markers'))
            
            if custom == 1:
                d = fig.add_trace(go.Scatter(x = (custom_portfolio_metrics[1], np.nan) , y = (custom_portfolio_metrics[0], np.nan), mode = 'markers'))
                st.plotly_chart(d)

            elif custom == 0:
                st.plotly_chart(c)
        

            return min_risk, max_return, max_sharpe, portfolio_weights, weights

        # Executing efficient_frontier funciton---------------------------------------------------------------------------
        a_exec = efficient_frontier(N, RF, custom_toggle, lock_toggle)
        min_risk = pd.DataFrame({'Min Risk' : a_exec[0]})
        max_return = pd.DataFrame({'Max Return' : a_exec[1]})
        max_sharpe = pd.DataFrame({'Max Sharpe Ratio' : a_exec[2]})

        final_portfolios_df = pd.concat([min_risk, max_return, max_sharpe], axis = 1)
        weights_df = pd.DataFrame(a_exec[3], columns = ticker_selection)
        final_portfolios_df = final_portfolios_df.drop('Weights', axis = 0)

        st.subheader('Weights of the required Portfolios')
        tmp_df_wts = a_exec[4]

        if lock_toggle == 1:
            tmp_df_wts.columns = item_list + lock_toggle_ticker_list
            st.dataframe(tmp_df_wts)
        else:
            st.dataframe(tmp_df_wts)
        
        st.subheader("Portfolio Metrics")
        st.write(final_portfolios_df)

    ######################################################################################################################

    choice = st.sidebar.selectbox('Ticker Name', ticker_selection)

    #####################################################################################################################
    #####################################################################################################################
    #####################################################################################################################
    # Page  1 Tab 3 -  ###################################################################################################
    if tab3.button('Miscellaneous Analysis'):
        st.title('Yahoo Finance Information Sheet')
        # choice = st.selectbox('Ticker', ticker_selection)
        
        ticker_info = yf.Ticker(choice)
        st.header('Quarterly Balance Sheet')
        st.write(ticker_info.quarterly_balance_sheet)
        
        st.header('Quarterly Financials')
        st.write(ticker_info.quarterly_financials)

        st.header('Quarterly Cash Flows')
        st.write(ticker_info.quarterly_cashflow)

    #######################################################################################################################


elif page == 'Page 2':
    st.title('Risk Metrics')
    ticker = st.selectbox(label = 'Select Ticker', options = ticker_selection)

    # Fitting the distribution to data------------------------------------------------------------------------------
    f = Fitter(data = df_returns[ticker], distributions = ['norm', 't', 'nct', 'beta'])

    # distribution fitting
    def distribution_fitting(data, dist = 'nct', conf_interval = 0.99):

        x_quantile = np.linspace(np.min(data), np.max(data), len(data))
        var_historic = np.quantile(data, (1 - conf_interval))

        if dist == 'norm':
            param = f.fitted_param[dist]
            param_df = pd.DataFrame(param, index = ['Mean', 'Std Deviation'], columns = ['Paramaeters'])
            a_tmp = norm.pdf(x_quantile, loc = param[0], scale = param[1])
            var_parametric = norm.ppf(1 - conf_interval, loc = param[0], scale = param[1])
        
        elif dist == 't':
            param = f.fitted_param[dist]
            param_df = pd.DataFrame(param, index = ['Location', 'Scale', 'Kurtosis'], columns = ['Paramaeters'])
            a_tmp = t.pdf(x_quantile, param[0], param[1], param[2])
            var_parametric = t.ppf(1 - conf_interval, param[0], param[1], param[2])

        elif dist == 'nct':
            param = f.fitted_param[dist]
            param_df = pd.DataFrame(param, index = ['Location', 'Scale', 'Kurtosis', 'Skewness'], columns = ['Paramaeters'])
            a_tmp = nct.pdf(x_quantile, param[0], param[1], param[2], param[3])
            var_parametric = nct.ppf(1 - conf_interval, param[0], param[1], param[2], param[3])
        
        elif dist == 'beta':
            param = f.fitted_param[dist]
            param_df = pd.DataFrame(param, index = ['Alpha', 'Beta', 'Location', 'Scale'], columns = ['Paramaeters'])
            a_tmp = beta.pdf(x_quantile, param[0], param[1], param[2], param[3])
            var_parametric = beta.ppf(1 - conf_interval, param[0], param[1], param[2], param[3])
        
        return x_quantile, a_tmp, param_df, var_historic, var_parametric
        
    f.fit()

   # tmp_fig = distribution_fitting(df_returns[ticker], opt)

    col_dist1, col_dist2, col_dist3 = st.columns(3)
    opt = col_dist1.selectbox("Distribution Choices", ['norm', 't', 'nct', 'beta'])
    col_dist2.write(f.summary(method = 'aic'))
    col_dist3.write(distribution_fitting(df_returns[ticker], opt)[2])
    # col_dist3.table(f.fitted_param[opt])

    var_historic = distribution_fitting(df_returns[ticker], opt)[3]
    var_parametric = distribution_fitting(df_returns[ticker], opt)[4]

    # Plotly Plot of histogram and fitted distribution ---------------------------------------------------------------------
    tmp_fig = distribution_fitting(df_returns[ticker], opt)
    fig = go.Figure()
    fig.add_trace(go.Histogram(x = df_returns[ticker], name = ticker, histnorm = 'probability density'))
    fig.add_trace(go.Scatter(x = tmp_fig[0], y = tmp_fig[1], name = opt))

    st.plotly_chart(fig)

    #st.metric(label = VaR Historc, value = )

    conf, var1, var2,  = st.columns(3)
    conf_interval = conf.slider(label = 'Confidence Interval', min_value = 0.50, max_value = 0.99, step = 0.01)
    var1.metric(label = "VaR Historic", value = f"{np.round(distribution_fitting(df_returns[ticker], opt, conf_interval)[3], 4) * -100}%")
    var2.metric(label = "VaR Parametric", value = f"{np.round(distribution_fitting(df_returns[ticker], opt, conf_interval)[4], 4) * -100}%")


    st.header("Black Scholes Merton Framework to Estimate Price Fluctuations")

    def bsm_estimation_price(data, data2, T = 5, change = 10):
        # r = 0.02 * T
        r = (np.mean(data2)) * T
        if r < 0:
            r = 0
        else:
            r = r
        # sigma = 0.15 * T
        sigma = (np.std(data2)) * T

        K = data[-1]
        S = K * (1 + (change/100))

        d1 = (sigma * np.sqrt(T)) ** -1 * ((np.log(S/K)) + (r + 0.5 * sigma ** 2) * T)
        d2 = d1 - sigma * np.sqrt(T)

        d1 = norm.pdf(d1, r,sigma) * 100
        d2 = norm.pdf(d2, r,sigma) * 100

        return d1, d2, r, sigma

    bsm1, bsm2 = st.columns(2)
    price_change = bsm1.slider(label = "Percent Increase in Close Price", min_value = 5, max_value = 100, value = 5, step = 5)
    t = bsm2.slider(label = "Time Frame (Days)", min_value = 5, max_value = 252, value = 10, step = 5)


    bsm3, bsm4 = st.columns(2)
    bsm3.metric(label = "Probability of Positive Performance", value = f"{np.round(bsm_estimation_price(df_1[ticker], df_returns[ticker], T = t, change = price_change)[0], 2)}%")
    bsm4.metric(label = "Probability of Negative Performance", value = f"{np.round(bsm_estimation_price(df_1[ticker], df_returns[ticker], T = t, change = price_change)[1], 2)}%")

elif page == 'Page 3':
    st.write('Test 3')    