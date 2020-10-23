from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

import requests
from bs4 import BeautifulSoup

import random
import pandas as pd
import time


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


def load_summary(num_files) -> object:
    summary_metrics = list()
    company_names = download_sp500(num_files)
    for company, value in company_names.items():
        data_from_indv_company = summary_data(company)
        data_from_indv_company['company_name'] = value[0]
        data_from_indv_company['industry_type'] = value[-1]
        summary_metrics.append(data_from_indv_company)
    m_summary_metrics_df = pd.DataFrame(summary_metrics)
    m_summary_metrics_df.to_csv("summary_data.csv")
    return m_summary_metrics_df


def summary_data(company_name):
    url = f'https://financialmodelingprep.com/financial-summary/{company_name}'
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    browser = webdriver.Chrome('/usr/bin/chromedriver', options=options)
    browser.get(url)
    time.sleep(5)
    # element = WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "financial_summary")))
    soup = BeautifulSoup(browser.page_source)
    # resp = requests.get(f'https://financialmodelingprep.com/financial-summary/{company_name}')
    # soup = BeautifulSoup(resp.text, 'html.parser')
    metric_tables = soup.find("div", {"id", "financial-summary"})
    # table_list = element.get_attribute('table')
    # table_list = browser.find_element_by_id('financial_summary')
    summary = {}
    table_list = metric_tables.findAll('table', attrs={'class': 'table'})
    for table in table_list:
        for elements in table.findAll('tr'):
            key = elements.findAll("th")[0].text
            value = elements.findAll("td")[0].text
            try:
                summary[key] = value_to_float(value)
            except KeyError:
                print("Key not found")
            except ValueError:
                pass
    return summary


if __name__ == "__main__":

    output_frame = load_summary(num_files=50)
    print(output_frame)