import logging
import pandas as pd
import json

from fastapi import APIRouter, HTTPException
from app.helpers import *
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# variables loaded in from .env file to create the DB connection
SAVER_USERNAME = os.environ.get("SAVER_USERNAME")
SAVER_PASSWORD = os.environ.get("SAVER_PASSWORD")
SAVER_DB_HOST = os.environ.get("SAVER_DB_HOST")
SAVER_DB_NAME = os.environ.get("SAVER_DB_NAME")

log = logging.getLogger(__name__)
router = APIRouter()


@router.get('/dashboard/{bank_account_id}')
async def dashboard(bank_account_id: int):
    """
    Return key information for user dashboard
    
    ### Path Parameter
    `bank_account_id`: unique bank acount id number
    
    ### Response
    JSON string including transactions (Date, Category, Amount), spend_earn_ratio
    (null if user doesn't have one), and current balance and type of account
    that is linked.
    """
    
    # load user's transactions into dataframe
    transactions = load_user_data(bank_account_id)
    
    # throw error if user doesn't exist
    if len(transactions) == 0:
        raise HTTPException(
            
            status_code=404, detail=f"Bank Account ID, {bank_account_id}, doesn't exist")
    
    # drop columns not needed
    transactions.drop(columns=['parent_category_name', 'grandparent_category_name'],
                      inplace=True)
    
    # sort so that most recent transactions are at the top
    transactions.sort_values(by='date', ascending=False, inplace=True)
    
    # Rename columns
    transactions.rename(columns={
        'category_name': 'Category',
        'date': 'Date',
        'amount_dollars': 'Amount($)'},
                        inplace=True)
    
    # Reorder columns
    transactions = transactions[['Date', 'Category', 'Amount($)']]
    
    # Reverse spending to be a negative amount
    transactions['Amount($)'] = transactions['Amount($)'] * -1
    
    # reformat date column to just be MM/DD/YY
    transactions['Date'] = transactions["Date"].dt.strftime("%m/%d/%y")
    
    # create connection to saverlife DB
    conn = psycopg2.connect(user=SAVER_USERNAME, password=SAVER_PASSWORD,
                            host=SAVER_DB_HOST, dbname=SAVER_DB_NAME)
    
    # get user id based on bank id given
    query1 = f"""
    SELECT
        user_id
    FROM
        bank_accounts
    INNER JOIN
        plaid_financial_authentications ON plaid_financial_authentications.id=bank_accounts.plaid_financial_authentication_id
    WHERE
        bank_accounts.id = {bank_account_id};
    """
    user_id = pd.read_sql(query1, conn)
    user_id_number = user_id['user_id'].iloc[0]
    
    # get spend_earn_ratio of user for the latest 12 months we have data for
    query2 = f"""
    SELECT
        user_id, spend_earn_ratio
    FROM
        transactional_financial_health_scores
    WHERE
        user_id = {user_id_number}
    ORDER BY
        run_date DESC
    LIMIT 1;
    """
    profile = pd.read_sql(query2, conn)
    spend_earn_dict = {}
    if len(profile) == 0:
        spend_earn_dict['spend_earn_ratio'] = None
    else:
        spend_earn_dict['spend_earn_ratio'] = profile['spend_earn_ratio'].iloc[0]
    
    # get current account balance (val) and account type (key) and put into dictionary
    query3 = f"""
    SELECT
        current_balance_cents, account_subtype
    FROM
        bank_accounts
    WHERE
        id = {bank_account_id}
    """
    current_balance = pd.read_sql(query3, conn)
    
    # create dictionary showing user's account type
    account_type_dict = {'account_type': current_balance['account_subtype'].iloc[0]}

    # create dictionary showing user's current balance
    current_balance_dict = {'current_balance': current_balance['current_balance_cents'].iloc[0]/100}

    # close DB connection
    conn.close()

    return json.dumps([transactions.to_json(), spend_earn_dict,
                       account_type_dict, current_balance_dict])
