import requests
import os
import datetime as dt
import news_article
from news_article import strip_tags
import json

stock_price_url = "https://www.alphavantage.co/query"
news_url = "https://newsapi.org/v2/everything"
stock_ticker_symbol_url = "https://yfapi.net/v6/finance/autocomplete"
API_PRICE_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
API_YAHOO_KEY = os.environ.get("YAHOO_API_KEY")
API_NEWS_KEY = os.environ.get("NEWS_API_KEY")

EMOJIS = ["🟢", "🔴"]


def get_stock_ticker_symbol(company_name):
    company_list = []
    data = {}
    try:
        with open("stock_ticker_symbols.json", mode="r") as data_file:
            data = json.load(data_file)
            company_list = data.keys()
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        open("stock_ticker_symbols.json", mode="a")
    finally:
        if company_name not in company_list:
            headers = {
                'x-api-key': API_YAHOO_KEY
            }
            params = {
                "query": company_name,
                "lang": "en"
            }

            response = requests.request("GET", stock_ticker_symbol_url, headers=headers, params=params)
            response.raise_for_status()
            if len(response.json().get("ResultSet").get("Result")) == 0:
                return ""
            stock_ticker_symbol = "AAPL"  # response.json().get("ResultSet").get("Result")[0].get("symbol")
            data[company_name] = stock_ticker_symbol
            with open(file="stock_ticker_symbols.json", mode="w") as data_file:
                json.dump(data, data_file, indent=4)
        else:
            return data.get(company_name)


# ----------------------------------- STOCK NEWS ----------------------------------------#

def get_stock_news(company):
    yesterday = str(dt.datetime.now() - dt.timedelta(days=1)).split(".")[0]

    answer = requests.get(
        url=f"{news_url}?q={company}&apiKey={API_NEWS_KEY}&searchIn=title&from={yesterday}&pageSize=3&sortBy"
            f"=popularity&page=1&language=en")
    answer.raise_for_status()
    articles_raw_list = answer.json().get("articles")
    articles_list = [
        news_article.Article(title=strip_tags(article.get("title")), description=strip_tags(article.get("description")),
                             source=article.get("url")) for article in articles_raw_list[:2]]
    if len(articles_list) == 0:
        return f"\nCannot find any news about \"{company}\". Please check if it's spelled correctly."
    stock_news = ""
    for article in articles_list:
        stock_news += f"\n{article}\n"
    return stock_news


# ----------------------------------- STOCK PRICE -----------------------------------------#
# Use this if you wan't your result based on another currency
# CURRENCY = "EUR"
# def get_currency_exchange_rate():
#     currency_exchange_rate = requests.get(
#         url=f"{stock_price_url}?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency={CURRENCY}&apikey={API_PRICE_KEY}")
#     currency_exchange_rate.raise_for_status()
#     currency_exchange_rate = currency_exchange_rate.json().get("Realtime Currency Exchange Rate")
#     return float(currency_exchange_rate.get("5. Exchange Rate"))


def get_price_data(currency_exchange_rate, stock):
    answer_price_data = requests.get(url=f"{stock_price_url}?function=TIME_SERIES_DAILY&symbol={stock}&interval=60min"
                                         f"&datatype=json&apikey={API_PRICE_KEY}")
    answer_price_data.raise_for_status()
    answer_price_data = answer_price_data.json().get("Time Series (Daily)")
    date = list(answer_price_data.keys())[0]
    open_price = float(answer_price_data.get(date).get("1. open")) * currency_exchange_rate
    closing_price = float(answer_price_data.get(date).get("4. close")) * currency_exchange_rate
    percentage = (closing_price / open_price - 1) * 100
    return open_price, closing_price, percentage, date


def get_stock_price_string(stock):
    price_data = get_price_data(1, stock)
    if price_data[2] < 0:
        return f"{EMOJIS[1]} {round(price_data[2], 2)}% ({price_data[3]})"
    else:
        return f"{EMOJIS[0]} {round(price_data[2], 2)}% ({price_data[3]})"


# ----------------------------------------------------------------------------#

def get_all_data(company_name):
    max_trys = 10
    for trys in range(0, max_trys):
        try:
            stock_name = get_stock_ticker_symbol(company_name)
            if stock_name == "":
                return f"Something went wrong. Please check if \"{company_name.title()}\" is spelled correctly."
            stock_price = get_stock_price_string(stock_name)
            stock_news = get_stock_news(company_name)
        except (requests.exceptions.RequestException, AttributeError) as e:
            if trys < max_trys - 1:
                pass  # try another time
            else:
                print(e)
                return f"Something went wrong ({print(e)}). Please check if \"{company_name.title()}\" is spelled correctly."
        else:
            return f"{company_name.title()}:\n{stock_price}\n{stock_news}"
