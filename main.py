import streamlit as st
import requests
from bs4 import BeautifulSoup
import pickle
from fmp_python.fmp import FMP
import time
import datetime
import os
from pathlib import Path

import pandas as pd
import numpy as np

import altair as alt
import itertools
import random
from scrapeYahoo import load_summary

fmp = FMP(api_key='14b4fa2d27fbcd148244dec7b578caa7')


def download_sp500(num_sample):
    resp = requests.get('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = BeautifulSoup(resp.text)
    table = soup.find('table', {'class': 'wikitable sortable'})
    num_samples = num_sample
    tickers = {}
    for row in table.findAll('tr')[1:]:
        row_contents = row.findAll('td')
        name = row_contents[0].text.strip()
        company_name = row_contents[1].text.strip()
        industry_type = row_contents[3].text.strip()
        tickers[name] = (company_name, industry_type)
    tickers = dict(random.sample(tickers.items(), num_samples))
    return tickers


# def value_to_float(value):
#     """Argument:
#     value : (String) Digits converted to striing
#     """
#     try:
#         if "," in value:
#             value = value.replace(",", "")
#
#         if '$' in value:
#             value = value.replace("$", "")
#
#         if type(value) == float or type(value) == int:
#             return value
#
#         if 'K' in value:
#             if len(value) > 1:
#                 return float(value.replace('K', '')) * 1000
#             return 1000
#
#         if 'B' in value:
#             if len(value) > 1:
#                 return float(value.replace('B', '')) * 1000000000
#             return 1000000000
#
#         if 'M' in value:
#             if len(value) > 1:
#                 return float(value.replace('M', '')) * 1000000
#             return 1000000
#
#         if '%' in value:
#             return round(float(value.replace('%', '')) / 100, 4)
#
#         else:
#             return float(value)
#
#     except:
#         return value
#
#
# @st.cache
# def load_summary(num_files):
#     summary_metrics = list()
#     company_names = download_sp500(num_files)
#     for company, value in company_names.items():
#         data_from_indv_company = summary_data(company)
#         data_from_indv_company['company_name'] = value[0]
#         data_from_indv_company['industry_type'] = value[-1]
#         summary_metrics.append(data_from_indv_company)
#     m_summary_metrics_df = pd.DataFrame(summary_metrics)
#     m_summary_metrics_df.to_csv("summary_data.csv")
#     return m_summary_metrics_df
#
#
# @st.cache
# def summary_data(company_name):
#     url = f'https://financialmodelingprep.com/financial-summary/{company_name}'
#     browser = webdriver.PhantomJS()
#     browser.get(url)
#     try:
#         element = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.NAME, "financial_summary")))
#     finally:
#         browser.quit()
#     # soup = BeautifulSoup(browser.page_source)
#     # resp = requests.get(f'https://financialmodelingprep.com/financial-summary/{company_name}')
#     # soup = BeautifulSoup(resp.text, 'html.parser')
#     # metric_tables = soup.find("div", {"id", "financial-summary"})
#     table_list = element.get_attribute('table')
#     summary = {}
#     # table_list = metric_tables.findAll('table', attrs={'class': 'table'})
#     for table in table_list:
#         for elements in table.findAll('tr'):
#             key = elements.findAll("th")[0].text
#             value = elements.findAll("td")[0].text
#             try:
#                 summary[key] = value_to_float(value)
#             except KeyError:
#                 print("Key not found")
#             except ValueError:
#                 pass
#     return summary


if __name__ == "__main__":
    # TODO: only load data if it is present
    st.title('Standard & Poor 500 Companies')
    data_load_state = st.text('Loading data...')
    s_n_p_file = Path('summary_data.csv')
    # click the refresh button to see when the file was last updated
    if st.button("Refresh"):
        try:
            absolute_path = s_n_p_file.resolve(True)
            last_modified_time = absolute_path.stat().st_mtime
            last_modified_date = datetime.datetime.fromtimestamp(last_modified_time)
            difference = datetime.datetime.now() - last_modified_date
            if difference.days > 1:
                data_load_state.text('Loading data...done!')
                summary_metrics_df = load_summary(200)

            else:
                # if the file does not need to be modified, just load the existing file
                summary_metrics_df = st.cache(pd.read_csv)("summary_data.csv")
        except FileNotFoundError:
            print(FileNotFoundError)
            summary_metrics_df = load_summary(200)
    elif s_n_p_file.is_file():
        # cache the data
        summary_metrics_df = st.cache(pd.read_csv)("summary_data.csv")
    else:
        summary_metrics_df = load_summary(200)
    data_load_state.text('Loading data...done!')
    ########################################################
    # write the raw data
    if st.checkbox('Show raw data'):
        st.title('Raw data')
        st.write(summary_metrics_df)

    ########################################################
    # Allow the users to select the names of the company
    names_of_the_company = st.sidebar.multiselect("Enter names of the company", summary_metrics_df['company_name'].unique())
    st.write("Your selected companies are", summary_metrics_df[summary_metrics_df['company_name']
             .isin(names_of_the_company)][['Symbol', 'industry_type']])
    # now select the metrics users want to use
    # metric_list: list = st.selectbox("Which metrics would you want to consider for the evaluation?",
    #                                  ("P/E", "Debt / Equity", "ROE", "ROA", "Market Cap", "Price"))
    metric_list: list = st.multiselect("Which metrics would you want to consider for the evaluation?",
                                     ("Beta (5Y Monthly)","PE Ratio (TTM)", "EPS (TTM)"))
    st.write('You selected:', metric_list)
    #########################################################
    st.subheader("Value of the shortlisted stocks")
    selected_company_data = summary_metrics_df[summary_metrics_df['company_name'].isin(names_of_the_company)]
    select_company_data = selected_company_data[['company_name', 'Previous Close', 'Open','52 Week Range',
                                                 "Forward Dividend & Yield","Ex-Dividend Date",
                                                 "Beta (5Y Monthly)","PE Ratio (TTM)", "EPS (TTM)"]]
    if metric_list:
        select_company_data_sorted = select_company_data.sort_values(by=metric_list[0], ascending=False)
    else:
        select_company_data_sorted = select_company_data
    if st.checkbox('Show raw data from the selected '):
        st.write(select_company_data_sorted)
    #####################################################
    if st.checkbox(f"Display the {metric_list[0]} graph") and metric_list:
        st.altair_chart(alt.Chart(selected_company_data).mark_bar()
                    .encode(x=alt.X('company_name', sort=alt.SortField(field=metric_list[0], order='descending'),
                                    axis=alt.Axis(title='Company Name')),
                            y=alt.Y(metric_list[0] + ":Q", axis=alt.Axis(title=metric_list[0])),
                            color='Symbol:N').interactive(), use_container_width=True)

    if len(metric_list)>1 and st.checkbox(f"Display the {metric_list[1]} graph"):
        st.altair_chart(alt.Chart(selected_company_data).mark_bar()
                        .encode(x=alt.X('company_name', sort=alt.SortField(field=metric_list[1], order='descending'),
                        axis=alt.Axis(title='Company Name')),
                        y=alt.Y(metric_list[1] + ":Q", axis=alt.Axis(title=metric_list[1])),
                        color='Symbol:N').interactive(), use_container_width=True)

