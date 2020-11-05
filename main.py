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
from scrapeYahoo import load_summary, download_historical_price

from collections import Counter
import csv


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


@st.cache
def load_favorites(tickers, number_of_clicks=20):
    """Count the number of clicks and return the favorites"""
    counter_per_ticker = Counter(tickers)
    list_of_favorites = list()
    for name_stock, count in counter_per_ticker.items():
        if count > number_of_clicks:
            list_of_favorites.append(name_stock)
    return list_of_favorites


def save_the_favorites(names_of_company):
    names_of_company = set(names_of_company)
    click_per_stick = dict()
    if os.path.exists("clicks.csv"):
        try:
            with open("clicks.csv",'r') as file_obj:
                first = file_obj.read(1)
                if not first:
                    for name in names_of_company:
                        click_per_stick[name] = 1
                else:
                    for line in file_obj:
                        name, count = line.split(",")
                        click_per_stick[name] = float(count)
                        if name in names_of_company:
                            click_per_stick[name] += 1
        except:
                for name in names_of_company:
                    click_per_stick[name] = 1

        finally:
            with open("clicks.csv", "w") as fileobj:
                 for name in names_of_company:
                    clicks = click_per_stick.get(name,1)
                    fileobj.write(f"{name},{clicks}\n")

    else:
        with open("clicks.csv", "w") as fileobj:
            for name in names_of_company:
                fileobj.write(f"{name},1\n")


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
    names_of_the_company = st.sidebar.multiselect("Enter names of the company", sorted(summary_metrics_df['company_name'].unique()))
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
    if metric_list and st.checkbox(f"Display the {metric_list[0]} graph") :

        st.altair_chart(alt.Chart(selected_company_data).mark_bar()
                    .encode(x=alt.X('company_name', sort=alt.SortField(field=metric_list[0], order='descending'),
                            axis=alt.Axis(title='Company Name')),
                            y=alt.Y(metric_list[0] + ":Q", axis=alt.Axis(title=metric_list[0])),
                            tooltip=[alt.Tooltip('company_name'),
                                     alt.Tooltip("PE Ratio (TTM)"),
                                     alt.Tooltip("52 Week Range"),
                                     alt.Tooltip("Forward Dividend & Yield")],
                            color='Symbol:N').interactive(), use_container_width=True)
        save_the_favorites(names_of_the_company)

    if len(metric_list)>1 and st.checkbox(f"Display the {metric_list[1]} graph"):
        st.altair_chart(alt.Chart(selected_company_data).mark_bar()
                        .encode(x=alt.X('company_name', sort=alt.SortField(field=metric_list[1], order='descending'),
                        axis=alt.Axis(title='Company Name')),
                        y=alt.Y(metric_list[1] + ":Q", axis=alt.Axis(title=metric_list[1])),
                        tooltip=[alt.Tooltip('company_name'),
                                 alt.Tooltip('Beta (5Y Monthly)')],
                        color='Symbol:N').interactive(), use_container_width=True)

    company_4_hist_data = st.sidebar.selectbox("Enter company for historical data", sorted(summary_metrics_df['company_name'].unique()))
    symbol_4_hist_data = summary_metrics_df.loc[summary_metrics_df["company_name"] == company_4_hist_data,"Symbol"].values[0]
    if st.button("Plot history"):
        progress_bar = st.progress(0)
        download_historical_price(symbol_4_hist_data)
        for percent_complete in range(100):
            time.sleep(0.1)
            progress_bar.progress(percent_complete + 1)
        hist_df = st.cache(pd.read_csv)(f"./price/{symbol_4_hist_data}.csv")
        # melt the data so that columns are rows
        hist_df["Date"] = pd.to_datetime(hist_df["Date"]).dt.date
        hist_df = hist_df[["Date", "Open", "Close"]].melt("Date")

        st.altair_chart(alt.Chart(hist_df).mark_line().encode(x='Date',
                                                              y='value',
                                                              color='variable').interactive(), use_container_width=True)





