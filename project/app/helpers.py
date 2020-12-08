import pandas as pd
import os
from sqlalchemy import create_engine
import psycopg2
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

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
    # currently sets category_name to parent_category_name
    conn1 = psycopg2.connect(user=SAVER_USERNAME, password=SAVER_PASSWORD,
                             host=SAVER_DB_HOST, dbname=SAVER_DB_NAME)
    
    query = open('app/query.sql').read() + str(bank_id)
    df = pd.read_sql(query, conn1)
    conn1.close()
    df = df[['category_id','amount_cents','date', 'grandparent_category_name',
             'parent_category_name']]
    df['category_name'] = df.parent_category_name
    df['amount_dollars'] = df['amount_cents'] / 100
    df.drop(columns=["amount_cents"], inplace=True)
    return df
