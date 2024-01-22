import requests
import psycopg2
from sqlalchemy import create_engine #pip install both packages
import pandas as pd
from forex_python.converter import CurrencyRates
from prefect import task,flow
#NOW WE BEGIN THE AUTOMATION

@task
def extract():
    #Set the base URL for CoinGecko API
    base_url = "https://api.coingecko.com/api/v3"

    #Specify the endpoint for fetching trending coins
    trennding_coins_endpoint = "/coins/markets"

    #Paremeters for API request

    params_trending_coins = {
        'vs_currency': 'usd',
        'order': 'volume_desc',
        'per_page': 10,
        'page': 1
    }

    #Send get request to api endpoint with specified parameters
    response = requests.get(base_url + trennding_coins_endpoint, params=params_trending_coins)

    #parse the json response to a python dictionary
    data_trending_coins = response.json()
    print('extracted')
    return data_trending_coins




@task
def transform(data_trending_coins):
    df = pd.DataFrame(data_trending_coins)

    #select the first 9 columns (index 0 to 8)
    df =  df.iloc[:, :9]
    # drop image column
    df = df.drop('image' , axis=1)

    #define the function that converts prices
    def convert_price(row, to_currency):
        c = CurrencyRates()

        #get current price from dataframe row
        price = row['current_price']
        #since our currency is in USD
        from_currency = 'USD'

        #FETCHING the exchange rates from CurrencyRates object
        exchange_rate = c.get_rate(from_currency,to_currency)

        #calculate the price
        converted_price = price * exchange_rate

        return converted_price

    #list of target currencies for conversion
    currencies = ['EUR', 'GBP', 'JPY']

    #iterate throught each target currency
    for currency in currencies:
        #apply the convert_price function to each row, creating new columns in the df dataframe
        df[f'price_in_{currency}'] = df.apply(lambda row: convert_price(row, currency),axis = 1)

    # we need a date column, we'll delete the former table in our database 
    today = pd.to_datetime('today')
    df[today] = today
    print('transformed')
    return df


@task
def load(dataframe):
    try:

        #Create a dictionary of our credentials
        connection_params = {
        "host": "testtech.postgres.database.azure.com",
        "port": "5432",
        "user": "testtech",
        "password": "Your_password",
        "database": "postgres"
    }

    #Create a SQLalchemy engine for connecting to database
        engine = create_engine(f'postgresql+psycopg2://{connection_params["user"]}:{connection_params["password"]}@{connection_params["host"]}:{connection_params["port"]}/{connection_params["database"]}')
    #Append the dataframe contents to the existing table and it'll create it if it's not there.
        dataframe.to_sql('trending_coins' , engine, if_exists = 'append', index = False)

        print('Database Successfully updated')

    except Exception as e:
        print('An error occurred:', e)

    finally:
        if engine:
            engine.dispose()


@flow
def trending_coins_flow():
    extract_data = extract()
    transform_data = transform.map(extract_data) #pass the extract_data to transform with .map
    load_data = load.map(transform_data)


if __name__ == "__main__":
    trending_coins_flow.serve(name = 'trending_coins_flow', interval = 3600)

# we need to start the prefect server first