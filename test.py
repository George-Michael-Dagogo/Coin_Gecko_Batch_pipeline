import requests
import pandas as pd
from currency_converter import CurrencyConverter





def extract():
    base_url = "https://api.coingecko.com/api/v3/"
    trending_coins_enpoint = "coins/markets"

    params_trending_coins= {
        "vs_currency" : 'usd',
        "order": "volume_desc",
        "per_page": 10,
        "page": 1
    }

    response = requests.get(base_url+trending_coins_enpoint, params = params_trending_coins)

    data_trending_coins = response.json()
    print('extracted successfully')
    return data_trending_coins



def transform(data):
    df = pd.DataFrame(data)
    df = df.iloc[:, list(range(9)) + [-1]]
    df = df.drop('image', axis=1)

    # Initialize CurrencyConverter
    c = CurrencyConverter()

    def convert_price(row, to_currency):
        price = row['current_price']
        from_currency = 'USD'
        try:
            converted_price = c.convert(price, from_currency, to_currency)
        except ValueError:
            # Handle case where conversion is not available
            converted_price = None
        return converted_price

    currencies = ['EUR', 'GBP', 'JPY']

    for currency in currencies:
        df[f'price_in_{currency}'] = df.apply(lambda row: convert_price(row, currency), axis=1)

    print('transformed successfully')
    return df


df = extract()
sd = transform(df)
print(sd)