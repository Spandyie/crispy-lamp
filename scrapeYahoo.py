from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

import random
import pandas as pd
import time
import requests

def value_to_float(value):
    """Argument:
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
        if 'T' in value:
            if len(value) > 1:
                return float(value.replace('T','')) * 1000000000000
            return 1000000000000

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



def download_sp500(num_sample: int) -> dict:
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


def scrape_yahoo(ticker):
    summary = {}
    summary["Symbol"]=ticker
    url = f'https://finance.yahoo.com/quote/{ticker}?p={ticker}'
    x_path_left = "/html/body/div[1]/div/div/div[1]/div/div[3]/div[1]/div/div[1]/div/div/div/div[2]/div[1]"
    x_path_right = '// *[ @ id = "quote-summary"]'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome('/usr/bin/chromedriver', options=options)
    browser.implicitly_wait(10)
    browser.get(url)
    element = browser.find_element_by_id("quote-summary")
    rows = element.find_elements_by_tag_name("tr")
    for row in rows:
        key = row.find_elements_by_tag_name("td")[0].text
        value = row.find_elements_by_tag_name("td")[1].text
        try:
            summary[key] = value_to_float(value)
        except ValueError:
            summary[key] = value
    return summary


def load_summary(num_files) -> object:
    summary_metrics = list()
    company_names = download_sp500(num_files)
    for company, value in company_names.items():
        data_from_indv_company = scrape_yahoo(company)
        data_from_indv_company['company_name'] = value[0]
        data_from_indv_company['industry_type'] = value[-1]
        summary_metrics.append(data_from_indv_company)
    m_summary_metrics_df = pd.DataFrame(summary_metrics)
    m_summary_metrics_df.to_csv("summary_data.csv")
    return m_summary_metrics_df


def download_historical_price(name_of_company):
    """
    Downloads the csv file of the histrcial stock proces
    Args name_of_company: String"""
    """download csv file for the historical price"""
    download_url = f"https://query1.finance.yahoo.com/v7/finance/download/{name_of_company}?period1=1446422400&period2=1604188800&interval=1d&events=history&includeAdjustedClose=true"
    req = requests.get(download_url)
    with open(f"./price/{name_of_company}.csv","wb") as file:
        file.write(req.content)




if __name__ == "__main__":
    summary = load_summary(10)
    print(summary)
