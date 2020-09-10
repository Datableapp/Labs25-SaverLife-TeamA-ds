import logging
import random

from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
# import operator
from app.helpers import *
from app.user import User
from pydantic import BaseModel, Field, validator
from typing import Optional

log = logging.getLogger(__name__)
router = APIRouter()



class Item(BaseModel):
    """Use this data model to parse the request body JSON."""

    x1: float = Field(..., example=3.14)
    x2: int = Field(..., example=-42)
    x3: str = Field(..., example='banjo')

    def to_df(self):
        """Convert pydantic object to pandas dataframe with 1 row."""
        return pd.DataFrame([dict(self)])

    @validator('x1')
    def x1_must_be_positive(cls, value):
        """Validate that x1 is a positive number."""
        assert value > 0, f'x1 == {value}, must be > 0'
        return value


class Budget(BaseModel):
    """Use this data model to parse the request body JSON."""

    bank_account_id: int = Field(..., example=131952)
    monthly_savings_goal: int = Field(..., example=50)
    placeholder: str = Field(..., example='banjo')

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


@router.post('/future_budget')
async def future_budget(budget: Budget):
    """
    Suggest a budget for a specified user.

    ### Request Body
    - `bank_account_id`: int
    - `monthly_savings_goal`: integer
    - `placeholder`: string

    ### Response
    - `category`: grandparent category name
    - `budgeted_amount`: integer suggesting the maximum the user should spend 
    in that catgory next month

    """

    # Get the JSON object from the POST request body and cast it to a python dictionary
    input_dict = budget.to_dict()
    bank_account_id = input_dict['bank_account_id']
    monthly_savings_goal = input_dict['monthly_savings_goal']

    transactions = load_user_data(bank_account_id)

    # instantiate the user
    user = User(transactions)

    return user.future_budget(monthly_savings_goal=monthly_savings_goal)


@router.get('/current_month_spending/{bank_account_id}')
async def current_month_spending(bank_account_id: str, day_of_month: Optional[int] = None):
    """
    Get user spending for the current month.

    ### Path Parameter
    - `bank_account_id`: int
    - `OPTIONAL: day_of_month`: int (0 - 31) - day of the month used to specify
    that you only want spending up to and including this specify day in the
    month

    ### Response
    - `category`: grandparent category name
    - `amount_spent`: integer showing amount the user has spent for each
    category in the latest month we have data for 
    """
    transactions = load_user_data(bank_account_id)

    if len(transactions) == 0:
        raise HTTPException(
            status_code=404, detail=f"Bank Account ID, {bank_account_id}, doesn't exist")

    user = User(transactions)
    
    if day_of_month:
        return user.current_month_spending(date_cutoff=day_of_month)
    else:
        return user.current_month_spending()
