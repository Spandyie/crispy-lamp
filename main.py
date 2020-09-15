
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pickle
from fmp_python.fmp import FMP

from urllib.request import urlopen
import json

import pandas as pd
import numpy as np

import altair as alt

fmp = FMP(api_key='14b4fa2d27fbcd148244dec7b578caa7')


def download_sp500():
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = BeautifulSoup(resp.text)
    table = soup.find('table', {'class': 'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.strip()

        tickers.append(ticker)

    with open("sp500tickers.pickle", "wb") as f:
        pickle.dump(tickers, f)

    return tickers


# def get_market_capitalization(company):
#     """
#         Receive the content of ``url``, parse it as JSON and return the object.
#
#         Parameters
#         ----------
#         url : str
#
#         Returns
#         -------
#         dict
#         """
#     api_key = '14b4fa2d27fbcd148244dec7b578caa7'
#     url = f"https://financialmodelingprep.com/api/v3/market-capitalization/{company}?apikey={api_key}"
#     response = urlopen(url)
#     data = response.read().decode("utf-8")
#     return json.loads(data)
#
#
# def get_summary_profile(company):
#     api_key = '14b4fa2d27fbcd148244dec7b578caa7'
#     url = f"https://financialmodelingprep.com/api/v3/quote/{company}?apikey={api_key}"
#     response = urlopen(url)
#     data = response.read().decode("utf-8")
#     summary_data = json.loads(data)
#
#
# def get_key_metric(company):
#     api_key = '14b4fa2d27fbcd148244dec7b578caa7'
#     url = f"https://financialmodelingprep.com/api/v3/key-metrics/{company}?apikey={api_key}"
#     response = urlopen(url)
#     data = response.read().decode("utf-8")
#     summary_data = json.loads(data)
#     return summary_data[0]
#

def value_to_float(value):
    """Arguement:
    value : (String) Digits converted to striing
    """
    try:
        if "," in value:
            value = value.replace(",", "")

        if '$' in value:
            value = value.replace("$", "")

        if type(value) == float or type(value) == int:
            return value

        if 'K' in value:
            if len(value) > 1:
                return float(value.replace('K', '')) * 1000
            return 1000

        if 'B' in value:
            if len(value) > 1:
                return float(value.replace('B', '')) * 1000000000
            return 1000000000

        if 'M' in value:
            if len(value) > 1:
                return float(value.replace('M', '')) * 1000000
            return 1000000

        if '%' in value:
            return round(float(value.replace('%', '')) / 100, 4)

        else:
            return float(value)

    except:
        return value

@st.cache
def summary_data(company_name):
    resp = requests.get(f'https://financialmodelingprep.com/financial-summary/{company_name}')
    soup = BeautifulSoup(resp.text, 'html.parser')
    metric_tables = soup.find("div", {"id", "financial-summary"})
    summary = {}
    table_list = metric_tables.findAll('table', attrs={'class': 'table'})
    for table in table_list:
        for elements in table.findAll('tr'):
            key = elements.findAll("th")[0].text
            value = elements.findAll("td")[0].text
            try:
                summary[key] = value_to_float(value)
            except:
                print("Keynot found")
    return summary


if __name__ == "__main__":
    #TODO: only load data if it is present
    #
    st.title('S&p500 Companies')
    data_load_state = st.text('Loading data...')
    summary_metrics = list()
    ticker = download_sp500()
    company_list = ticker[:200]
    for company in company_list:
        data_from_indv_company = summary_data(company)
        summary_metrics.append(data_from_indv_company)

    summary_metrics_df = pd.DataFrame(summary_metrics)
    summary_metrics_df.to_csv("summary_data.csv")
    data_load_state.text('Loading data...done!')
    ##########
    #cache the data
    #summary_metrics_df = st.cache(pd.read_csv)("summary_data.csv")
########################################################
    # write the raw data
    if st.checkbox('Show raw data'):
        st.title('Raw data')
        #st.write(summary_metrics.sort_values(by=['Dividends'], ascending=False))
        st.write(summary_metrics_df)

    ###
    ## Allow the users to select the names of the company
    names_of_the_company = st.sidebar.multiselect("Enter the names of the company", summary_metrics_df['Symbol'].unique())
    st.write("Your selected companies are", names_of_the_company)
    ## now select the metrics users want to use
    metric_list = st.selectbox("Which metrics would you want to consider for the evaluation?",
                          ("P/E", "Debt / Equity", "Dividend Yield", "Market Cap", "Price", "Dividend Yield"))
    st.write('You selected:', metric_list)
    ######################################################
    st.subheader("Value of the shortlisted stocks")
    selected_company_data = summary_metrics_df[summary_metrics_df['Symbol'].isin(names_of_the_company)]
    select_company_data = selected_company_data[["Symbol",metric_list]]
    if st.checkbox('Show raw data from the selected '):
        st.write(select_company_data)
    ###################
    st.altair_chart(alt.Chart(selected_company_data).mark_bar().encode(
        color="Symbol:N",
        x="Symbol:N",
        y=metric_list+":Q").interactive(), use_container_width=True)


