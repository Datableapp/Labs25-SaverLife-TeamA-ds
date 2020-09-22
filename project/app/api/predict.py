import logging
import random
import pandas as pd
import numpy as np
import json

from fastapi import APIRouter, HTTPException, Request, Header, Query
from app.helpers import *
from app.user import User
from pydantic import BaseModel, Field, validator
from typing import Optional, List

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

    # predict budget using time series model
    pred_bud = user.predict_budget()

    # if a fatal error was encountered, return no budget along with the warning list
    if user.warning == 2:
        return json.dumps([None, user.warning_list])

    # modify budget based on savings goal
    modified_budget = user.budget_modifier(pred_bud, monthly_savings_goal=monthly_savings_goal)

    # if a fatal error was encountered, return no budget along with the warning list
    if user.warning == 2:
        return json.dumps([None, user.warning_list])

    # if a non-fatal warning was encountered in predict_budget() or budget_modifier(), return the budget along with the warning list
    elif user.warning == 1:
        return json.dumps([modified_budget, user.warning_list])

    return modified_budget


@router.get('/current_month_spending/{bank_account_id}')
async def current_month_spending(bank_account_id: int, day_of_month: Optional[int] = None, categories: List[str] = Query(None)):

    transactions = load_user_data(bank_account_id)
    
    if len(transactions) == 0:
        raise HTTPException(
            status_code=404, detail=f"Bank Account ID, {bank_account_id}, doesn't exist")
        
    if not categories:
        raise HTTPException(
            status_code=404, detail=f"Please provide the categories that were in the user's budget")
    
    user = User(transactions)

    if day_of_month:
        return user.current_month_spending(fixed_categories=categories, date_cutoff=day_of_month)
    else:
        return user.current_month_spending(fixed_categories=categories)
