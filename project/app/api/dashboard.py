import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

from fastapi import APIRouter, HTTPException
from app.helpers import *
from app.user import User
from pydantic import BaseModel, Field, validator
from typing import Optional
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


class Item(BaseModel):
    """Use this data model to parse the request body JSON."""
    bank_account_id: int = Field(..., example=131952)
    graph_type: str = Field(..., example='pie')
    time_period: str = Field(..., example='week')
    color_template: Optional[str] = Field('Greens_r', example='Greens_r')
    hole: Optional[float] = Field(0.8, example = 0.8)

    def to_df(self):
        """Convert pydantic object to pandas dataframe with 1 row."""
        return pd.DataFrame([dict(self)])

    def to_dict(self):
        """Convert pydantic object to python dictionary."""
        return dict(self)

    @validator('bank_account_id')
    def user_ID_must_exist(cls, value):
        """Validate that user_id is a valid ID."""
        conn = psycopg2.connect(user=SAVER_USERNAME, password=SAVER_PASSWORD,
                             host=SAVER_DB_HOST, dbname=SAVER_DB_NAME)
        query = f"""
        SELECT id
        FROM PUBLIC.plaid_main_transactions 
        WHERE bank_account_id = {value}
        LIMIT 1
        """
        df = pd.read_sql(query, conn)
        conn.close()
        assert len(df) > 0, f'the bank_account_id {value} is invalid'
        return value


    @validator('color_template')
    def color_template_must_be_valid(cls, value):
        """Validate that the color_template value is valid"""
        color_template_set = set(
            ['Aggrnyl','Aggrnyl_r','Agsunset','Agsunset_r','Blackbody',
            'Blackbody_r','Bluered','Bluered_r','Blues','Blues_r','Blugrn',
            'Blugrn_r','Bluyl','Bluyl_r','Brwnyl','Brwnyl_r','BuGn','BuGn_r',
            'BuPu','BuPu_r','Burg','Burg_r','Burgyl','Burgyl_r','Cividis',
            'Cividis_r','Darkmint','Darkmint_r','Electric','Electric_r',
            'Emrld','Emrld_r','GnBu','GnBu_r','Greens','Greens_r','Greys',
            'Greys_r','Hot','Hot_r','Inferno','Inferno_r','Jet','Jet_r',
            'Magenta','Magenta_r','Magma','Magma_r','Mint','Mint_r','OrRd',
            'OrRd_r','Oranges','Oranges_r','Oryel','Oryel_r','Peach',
            'Peach_r','Pinkyl','Pinkyl_r','Plasma','Plasma_r','Plotly3',
            'Plotly3_r','PuBu','PuBuGn','PuBuGn_r','PuBu_r','PuRd','PuRd_r',
            'Purp','Purp_r','Purples','Purples_r','Purpor','Purpor_r',
            'Rainbow','Rainbow_r','RdBu','RdBu_r','RdPu','RdPu_r','Redor',
            'Redor_r','Reds','Reds_r','Sunset','Sunset_r','Sunsetdark',
            'Sunsetdark_r','Teal','Teal_r','Tealgrn','Tealgrn_r','Viridis',
            'Viridis_r','YlGn','YlGnBu','YlGnBu_r','YlGn_r','YlOrBr',
            'YlOrBr_r','YlOrRd','YlOrRd_r','algae','algae_r','amp','amp_r',
            'deep','deep_r','dense','dense_r','gray','gray_r','haline',
            'haline_r','ice','ice_r','matter','matter_r','solar','solar_r',
            'speed','speed_r','swatches','tempo','tempo_r','thermal',
            'thermal_r','turbid','turbid_r'])
        
        error_str = f'the color template, {value}, is invalid. Please see a list of valid templates at https://plotly.com/python/builtin-colorscales/#builtin-sequential-color-scales'
        assert value in color_template_set, error_str
        return value


class MoneyFlow(BaseModel):
    """Use this data model to parse the request body JSON."""
    bank_account_id: int = Field(..., example=131952)
    time_period: str = Field(..., example='week')

    def to_df(self):
        """Convert pydantic object to pandas dataframe with 1 row."""
        return pd.DataFrame([dict(self)])

    def to_dict(self):
        """Convert pydantic object to python dictionary."""
        return dict(self)

    @validator('bank_account_id')
    def user_ID_must_exist(cls, value):
        """Validate that user_id is a valid ID."""
        conn = psycopg2.connect(user=SAVER_USERNAME, password=SAVER_PASSWORD,
                             host=SAVER_DB_HOST, dbname=SAVER_DB_NAME)
        query = f"""
        SELECT id
        FROM PUBLIC.plaid_main_transactions 
        WHERE bank_account_id = {value}
        LIMIT 1
        """
        df = pd.read_sql(query, conn)
        conn.close()
        assert len(df) > 0, f'the bank_account_id {value} is invalid'
        return value


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
