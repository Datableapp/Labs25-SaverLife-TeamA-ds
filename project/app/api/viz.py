import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from fastapi import APIRouter, HTTPException
from app.helpers import *
from app.user import User
from pydantic import BaseModel, Field, validator

log = logging.getLogger(__name__)
router = APIRouter()


class Item(BaseModel):
    """Use this data model to parse the request body JSON."""
    user_ID: str = Field(..., example='1635ob1dkQIz1QMjLmBpt0E36VyM96ImeyrgZ')
    graph_type: str = Field(..., example='pie')
    time_period: str = Field(..., example='week')

    def to_df(self):
        """Convert pydantic object to pandas dataframe with 1 row."""
        return pd.DataFrame([dict(self)])

    def to_dict(self):
        """Convert pydantic object to python dictionary."""
        return dict(self)

    @validator('user_ID')
    def user_ID_must_exist(cls, value):
        """Validate that user_id is a valid ID."""
        # load sample data and create a set of the user ID's
        users = set(clean_data()['plaid_account_id'])
        assert value in users, f'the user_ID {value} is invalid'
        return value
    
class MoneyFlow(BaseModel):
    """Use this data model to parse the request body JSON."""
    user_ID: str = Field(..., example='1635ob1dkQIz1QMjLmBpt0E36VyM96ImeyrgZ')
    time_period: str = Field(..., example='week')

    def to_df(self):
        """Convert pydantic object to pandas dataframe with 1 row."""
        return pd.DataFrame([dict(self)])

    def to_dict(self):
        """Convert pydantic object to python dictionary."""
        return dict(self)

    @validator('user_ID')
    def user_ID_must_exist(cls, value):
        """Validate that user_id is a valid ID."""
        # load sample data and create a set of the user ID's
        users = set(clean_data()['plaid_account_id'])
        assert value in users, f'the user_ID {value} is invalid'
        return value


@router.post('/moneyflow')
async def moneyflow(moneyflow: MoneyFlow):
    """
    Visualize a user's money flow 📈
    ### Request Body
    - `User_ID`: str
    - `time_period`: str
    
    ### Response
    - `plotly object`:
    visualizing the user's money flow over the specified time period.
    """
    # Get the JSON object from the POST request body and cast it to a python dictionary
    input_dict = moneyflow.to_dict()
    user_id = input_dict['user_ID']
    time_period = input_dict['time_period']
    
    transactions = clean_data()
    unique_users = set(transactions['plaid_account_id'].unique())

    # Validate the user
    if user_id not in unique_users:
        raise HTTPException(
            status_code=404, detail=f'User {user_id} not found')

    user = User(user_id, transactions)
    return user.money_flow(time_period=time_period)


@router.post('/spending')
async def spending(item: Item):
    """
    Make visualizations based on past spending 📊
    ### Request Body
    - `User_ID`: str
    - `graph_type`: str
    - `time_period`: str
    ### Response
    - `plotly object`:
    visualizing the user's spending habits in the form of the selected graph
    type.
    """
    # Get the JSON object from the POST request body and cast it to a python dictionary
    input_dict = item.to_dict()
    user_id = input_dict['user_ID']
    graph_type = input_dict['graph_type']
    time_period = input_dict['time_period']
    # Everything below is copy and pasted code from the spending() function in viz.py
    transactions = clean_data()
    unique_users = set(transactions['plaid_account_id'].unique())

    # Validate the user
    if user_id not in unique_users:
        raise HTTPException(
            status_code=404, detail=f'User {user_id} not found')

    user = User(user_id, transactions)

    if graph_type == 'pie':
        return user.categorical_spending(time_period=time_period)

    if graph_type == 'bar':
        return user.bar_viz(time_period=time_period)
