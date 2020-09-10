import pandas as pd
import os
from sqlalchemy import create_engine
import psycopg2
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# variables loaded in from .env file to create the DB connection
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")

SAVER_USERNAME = os.environ.get("SAVER_USERNAME")
SAVER_PASSWORD = os.environ.get("SAVER_PASSWORD")
SAVER_DB_HOST = os.environ.get("SAVER_DB_HOST")
SAVER_DB_NAME = os.environ.get("SAVER_DB_NAME")


def convert_to_datetime(df, columns=[]):
    """
    Takes in a dataframe and a list of columns, and converts those columns to
    datetime format.

    Parameters:
            df (dataframe): a dataframe with time columns not in datetime
                            format
            columns (list): list of columns to be converted
    """
    for col in columns:
        df[col] = pd.to_datetime(df[col], infer_datetime_format=True)


def load_user_data(bank_id):

    conn1 = psycopg2.connect(user=SAVER_USERNAME, password=SAVER_PASSWORD,
                             host=SAVER_DB_HOST, dbname=SAVER_DB_NAME)
    query1 = f"""
    SELECT
        id,
        date,
        amount_cents,
        merchant_address,
        merchant_city,
        merchant_state,
        merchant_zip,
        category_id,
        purpose
    FROM 
        public.plaid_main_transactions
    WHERE
        bank_account_id = {bank_id}
    """
    df1 = pd.read_sql(query1, conn1)
    conn1.close()

    conn2 = psycopg2.connect(user = USERNAME, password = PASSWORD,
                             host = DB_HOST, dbname = DB_NAME)
    query2 = "SELECT * FROM category_lookups"
    df2 = pd.read_sql(query2, conn2)
    conn2.close()
    
    transactions_categorized = pd.merge(df1, df2,
                                        how='left',
                                        left_on=['category_id'],
                                        right_on=['plaid_category_id'])
    transactions_categorized = transactions_categorized[['category_name',
                                                         'parent_category_name',
                                                         'grandparent_category_name',
                                                         'amount_cents',
                                                         'date']]
    transactions_categorized['amount_dollars'] = transactions_categorized['amount_cents'] / 100
    transactions_categorized.drop(columns=["amount_cents"], inplace=True)

    return transactions_categorized
