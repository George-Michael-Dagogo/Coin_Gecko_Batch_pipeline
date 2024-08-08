import requests
import pandas as pd
from currency_converter import CurrencyConverter
import psycopg2
from sqlalchemy import create_engine
from prefect import task, flow


@task(retries=2, retry_delay_seconds=10)
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


@task(retries=2, retry_delay_seconds=10)
def transform(data):
    df = pd.DataFrame(data)
    df = df.iloc[:,list(range(9)) + [-1]]
    df = df.drop('image',axis=1)


    def convert_price(row, to_currency):
        c = CurrencyRates()
        price = row['current_price']
        from_currency = 'USD'
        exchange_rate = c.get_rate(from_currency,to_currency)
        converted_price = price * exchange_rate

        return converted_price

    currencies = ['EUR', 'GBP', 'JPY']

    for currency in currencies:
        df[f'price_in_{currency}'] = df.apply(lambda row: convert_price(row, currency), axis = 1)
    print('transformed successfully')
    return df


@task(retries=2, retry_delay_seconds=10)
def loading(dataframe):
    try:
        
        # Create a dictionary of database connection parameters
        connection_params = {
            "host": "testtech.postgres.database.azure.com",
            "port": "5432",
            "user": "testtech",
            "password": "Your_password",
            "database": "postgres"
        }

        # Create a SQLAlchemy engine for connecting to the database
        engine = create_engine(
            f'postgresql+psycopg2://{connection_params["user"]}:{connection_params["password"]}@{connection_params["host"]}:{connection_params["port"]}/{connection_params["database"]}'
        )

        # Append the DataFrame contents to the existing table
        dataframe.to_sql("trending_coins", engine, if_exists='append', index=False)

        print('Database successfully updated')

    except Exception as e:
        print("An error occurred:", e)
        # Optionally: Log the error for further analysis

    finally:
        # Close the database connection gracefully
        if engine:
            engine.dispose()

@flow
def the_flow():
    data = extract()
    dataframe = transform(data)
    loading(dataframe)

if __name__ == "__main__":
    the_flow()
