import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import datetime as dt

from math import ceil
from datetime import timedelta
from statsmodels.tsa.api import SimpleExpSmoothing, ExponentialSmoothing


def get_last_time_period(transaction_df, time_period='week'):
    """
    Given a dataframe of transactions and dates and a desired timeframe,
    return the dataframe containing only transactions within that time frame.

    By default, the time frame is a week. This can be changed using the
    "time_period" parameter.
    If time_period is set to 'all', return the dataframe sorted by date
    """

    # make a copy of the user's expenses dataframe
    transaction_df = transaction_df.copy()
    # sort by date from earlist to latest
    transaction_df = transaction_df.sort_values(by=['date'])
    # grab the lastest date recorded
    latest_time = transaction_df['date'].iloc[-1]

    # based on the time period, establish a cutoff in order to subset the data
    if time_period == 'day':
        cutoff = latest_time - timedelta(days=1)
    elif time_period == 'month':
        cutoff = latest_time - timedelta(days=30)
    elif time_period == 'week':
        cutoff = latest_time - timedelta(days=7)
    elif time_period == 'year':
        cutoff = latest_time - timedelta(days=365)
    elif time_period == 'all':
        return transaction_df
    else:
        raise ValueError(
            f"time_period must be one of 'day, week, month, year, or all'. Got {time_period} instead.")

    # subset the data based on the time frame
    subset = transaction_df[transaction_df['date'] > cutoff]

    return subset


def monthly_spending_totals(user_expenses_df, num_months=12, category='grandparent_category_name'):
    """
    Given a dataframe of user transactions with category and date information,
    return a dataframe with transaction amounts grouped by category and
    aggregated by month

    By default, only transactions from the past 12 months are used. This can
    be changed using the num_months parameter.
    By default, the "grandparent_category_name" feature is used to group
    transactions. This can be changed using the category parameter.
    """

    # ticker to track how many times we have iterated
    ticker = 0
    # latest month we have data on for user
    cur_month = user_expenses_df['date'].max().month
    # latest year we have data on for user
    cur_year = user_expenses_df['date'].max().year

    while ticker < num_months:
        # on first iteration
        if ticker == 0:

            # if cur_month is January
            if cur_month == 1:
                # set prev month to December
                prev_month = 12
                # subset user expenses to include data from Decemeber of the previous year
                user_exp_prev = user_expenses_df[
                    (user_expenses_df['date'].dt.month == (prev_month)) &
                    (user_expenses_df['date'].dt.year == (cur_year - 1))
                ]
                # group df by category and sum the amount spent
                prev = user_exp_prev.groupby([category]).sum()
                # reassign cur month (going back in time)
                cur_month = prev_month
                # reassign cur year (going back in time)
                cur_year -= 1

            else:
                # prev month is the month before the cur month
                prev_month = cur_month - 1
                # subset user expenses to include data from pervious month of current year
                user_exp_prev = user_expenses_df[
                    (user_expenses_df['date'].dt.month == (prev_month)) &
                    (user_expenses_df['date'].dt.year == cur_year)
                ]
                # group df by category and sum the amount spent
                prev = user_exp_prev.groupby([category]).sum()
                # reassign cur month (going back in time)
                cur_month -= 1

            # rename amount dollars column to the month/year spending
            datestring = f"{prev_month}/{str(cur_year)[2:]}"
            prev.rename(columns={'amount_dollars': datestring}, inplace=True)
            # advance the ticker
            ticker += 1

        else:
            # if cur_month is January
            if cur_month == 1:
                # set prev month to Decemeber
                prev_month = 12
                # subset user expenses to include data from Decemeber of the prvious year
                other = user_expenses_df[
                    (user_expenses_df['date'].dt.month == (prev_month)) &
                    (user_expenses_df['date'].dt.year == (cur_year - 1))
                ]
                other = other.groupby([category]).sum()
                # group df by category and sum the amount spent
                prev = pd.concat([prev, other], axis=1, sort=True)
                # reassign cur month (going back in time)
                cur_month = prev_month
                # reassign cur year (going back in time)
                cur_year -= 1
            else:
                # prev month is the month before the cur month
                prev_month = cur_month - 1
                # subset user expenses to include data from pervious month of current year
                user_exp_prev = user_expenses_df[
                    (user_expenses_df['date'].dt.month == (prev_month)) &
                    (user_expenses_df['date'].dt.year == cur_year)
                ]
                # group df by category and sum the amount spent
                other = user_exp_prev.groupby([category]).sum()
                # concatenate 2 subsetted dataframes
                prev = pd.concat([prev, other], axis=1, sort=True)
                # reassign cur year (going back in time)
                cur_month -= 1

            # rename amount dollars column to the month/year spending
            datestring = f"{prev_month}/{str(cur_year)[2:]}"
            prev.rename(columns={'amount_dollars': datestring}, inplace=True)
            # advance the ticker
            ticker += 1

    # Fill NaN values for categories without spending amounts in a given month
    prev.fillna(value=0, inplace=True)

    # Reformat the dataframe so that columns are categores and rows are months.
    cols = [prev.columns[i] for i in range(len(prev.columns)-1, -1, -1)]
    prev = prev[cols]
    prev = prev.transpose()

    return prev


def trimmer(budget_df, threshold_1=10, threshold_2=0, trim_name='mean', name='Misc.', in_place=True, save=False):
    """
    Given a dataframe of average spending history, combine rows with a mean below a given threshold into a single row.

    A threshold based on a percentage of total spending can be used by setting threshold_1 to a value between 0 and 1
    An optional second threshold can be set to check whether or not the new row should be added or discarded.
    By default, the function will trim the 'mean' column. A different column can be specified by setting the 'trim_name' parameter.
    The new row's name will default to "Misc." but can be set using the 'name' parameter.
    By default, this function will modify the dataframe in place. Set in_place to False to disable this.
    The discarded rows can be returned as a list by setting save to True. The return object will become a tuple
    with the first entry being the dataframe and the second entry being the list of discarded categories.
    """

    # use a copy if in_place is set to false
    if not in_place:
        budget_df = budget_df.copy()

    # if thresholds were set to fractions, then calculate fraction of total
    # average spending and re-assign thresholds
    if 0 < threshold_1 < 1:
        threshold_1 *= budget_df[trim_name].sum()
    if 0 < threshold_2 < 1:
        threshold_2 *= budget_df[trim_name].sum()

    # get budget categories
    categories = budget_df.index

    # track the eliminated categories and the sum of their means
    trimmed_cats = []
    trimmed_sum = 0

    # for each category, check if the mean is below threshold_1
    # if it is, update trimmed_cats and trimmed_sum then delete the row
    for cat in categories:
        mean = budget_df[trim_name][cat]

        if mean < threshold_1:
            trimmed_sum += mean
            trimmed_cats.append(cat)

            budget_df.drop(index=cat, inplace=True)

    # if trimmed_sum is greater than threshold_2, then we add a new row
    # containing the sum of the means from the deleted rows
    if trimmed_sum > threshold_2:
        new_row = [np.NaN] * (len(budget_df.columns)-1) + [trimmed_sum]
        budget_df.loc[name] = new_row

    # if save=True, then return both the budget_df and the deleted categories
    if save:
        return (budget_df, trimmed_cats)

    return budget_df


def dict_trimmer(budget, threshold_1=10, threshold_2=0, name='Misc.', in_place=True, save=False):
    """
    Given a spending budget dictionary, combine rows with a mean below a given threshold into a single row.

    A threshold based on a percentage of total spending can be used by setting threshold_1 to a value between 0 and 1
    An optional second threshold can be set to check whether or not the new row should be added or discarded.
    The new row's name will default to "Misc." but can be set using the 'name' parameter.
    By default, this function will modify the dictionary in place. Set in_place to False to disable this.
    The discarded rows can be returned as a list by setting save to True. The return object will become a tuple
    with the first entry being the dataframe and the second entry being the list of discarded categories.
    """
    # use a copy if in_place is set to false

    if not in_place:
        budget = budget.copy()

    print("")
    print(f"budget: {budget}")

    # if thresholds were set to fractions, then calculate fraction of total
    # spending and re-assign thresholds
    if 0 < threshold_1 < 1:
        total_budget = 0
        for cat in budget:
            total_budget += budget[cat]
        threshold_1 *= total_budget
    if 0 < threshold_2 < 1:
        total_budget = 0
        for cat in budget:
            total_budget += budget[cat]
        threshold_2 *= total_budget

    # get budget categories. Since we're modifying the budget dictioanry in
    # the below loop, we convert to list or use a copy of budget.
    categories = list(budget.keys())

    # track the eliminated categories and the sum of their budgeted amounts
    trimmed_cats = []
    trimmed_sum = 0

    # for each category, check if the budget_amount is below threshold_1
    # if it is, update trimmed_cats and trimmed_sum then delete the row
    for cat in categories:
        budget_amount = budget[cat]
        if budget_amount < threshold_1:
            trimmed_sum += budget_amount
            trimmed_cats.append(cat)
            del budget[cat]

    # if trimmed_sum is greater than threshold_2, then we add a new row
    # containing the sum of the means from the deleted rows
    if trimmed_sum > threshold_2:
        budget[name] = trimmed_sum

    # If save=True, then return both the budget and the deleted categories
    if save:
        return (budget, trimmed_cats)

    return budget


def drop_low_frequency_categories(total_spending_by_month_df, min_frequency=1):
    """
    Given a dataframe of budget categories aggregated by some time frame, drop columns with a number of zero values equal to or below the minimum frequency

    By default, the minimum frequency is 1 values. This can be changed using the min_frequency parameter.
    """

    # for each category in the dataframe, calculate the number of non-zero rows
    for cat in total_spending_by_month_df.columns:
        total_nonzeros = len(total_spending_by_month_df) - len(
            total_spending_by_month_df[total_spending_by_month_df[cat] == 0])

        # if the number of non-zero rows is equal to or less then the
        # min_frequency, drop the column
        if total_nonzeros <= min_frequency:
            total_spending_by_month_df.drop(columns=cat, inplace=True)


class User():
    """
    Class used to contain and analyze a user's transaction data

    Attributes:
        data (dataframe): dataframe of user's transactions
        name (str): user's name (optional)
        show (bool): set to True to display graphs after they are generated.
            Defaults to False.
        hole (float): sets size of the donut hole for the
            categorical_spending() charts
        expenses (dataframe): user data filtered down to transactions that are
            positive and are not transfers
        misc (list): list used to store the names of categories that are
            combined into the "Misc." category
        warning (int): warning flag used to indicate that an error has been
            encountered during budget generation
        warning_list (list): list used to contain warning messaged
    """

    def __init__(self, data, name=None, show=False, hole=0.8, cat_column='parent_category_name'):
        """
        Constructor for the User class.

        Parameters:
            data (dataframe): dataframe of user's transactions
            name (str): user's name (optional)
            show (bool): set to True to display graphs after they are
                generated. Defaults to False
            hole (float): sets size of the donut hole for the
                categorical_spending() charts
        """

        self.name = name
        if not self.name:
            self.name = 'Test User'
        self.data = data
        self.expenses = self.data[
            (self.data['grandparent_category_name'] != 'Transfers') &
            (self.data['amount_dollars'] > 0)
        ]
        self.show = show
        self.past_months = 12
        self.hole = hole
        self.misc = []
        self.warning = 0
        self.warning_list = []
        self.cat_column = cat_column

    def get_user_data(self):
        """
        Returns all the user's transactional data in the form of a dataframe.
        """
        return self.data

    def categorical_spending(self, time_period='week', category='grandparent_category_name', color_template='Magenta', trim=True):
        """
        Returns jsonified plotly object which is a pie chart of recent
        transactions for the User.

        Parameters:
            time_period (str): timeframe used to define "recent"
            category (str): the level of spending category to use.
            color_template (str): the plotly sequential color template to use
            trim (bool): trim and combine small spending categories into a
                single category

        Returns:
            Plotly object of a pie chart in json format
        """

        user_expenses = self.expenses.copy()

        # get a list of categories
        cat_count = self.expenses[category].value_counts(normalize=True)

        # filter down to recent transactions
        user_expenses = get_last_time_period(user_expenses, time_period)

        # combine transactions by category
        # required so that each color matches 1 category/label
        user_expense_grouped = user_expenses.groupby(
            [category]).sum()

        # for categories that fall under 2% of transactions, group them into
        # a miscellaneous category
        trimmer(user_expense_grouped, threshold_1=0.02,
                trim_name='amount_dollars')

        # get list of colors from the plotly's color templates
        color_list = eval('px.colors.sequential.' + color_template)

        # create pie/donut chart
        fig = go.Figure(data=[go.Pie(labels=user_expense_grouped.index,
                                     values=user_expense_grouped['amount_dollars'],
                                     hole=self.hole,
                                     marker_colors=color_list
                                     )])

        # force percents to be inside donut bars
        fig.update_traces(textposition='inside',
                          textfont_size=14, textinfo="percent")

        # add outline to graph objects
        fig.update_traces(marker=dict(line=dict(color='#626262', width=1.5)))

        # add title based on current time period being viewed
        if time_period == 'all':
            fig.update_layout(
                title={"text": f"Spending by Category", "x": 0.5, "y": 0.9},
                font_size=16,)

        else:
            fig.update_layout(title={
                              "text": f"Spending by Category for the Last {time_period.capitalize()}",
                              "x": 0.5, "y": 0.9},
                              font_size=16)

        # style the hover labels
        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"))

        # style the legend
        fig.update_layout(
            legend=dict(
                x=.43,
                y=.5,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,)))

        # Add shadow image under graph
        fig.add_layout_image(
            dict(
                source="https://raw.githubusercontent.com/KyleTy1er/Elwynn-Forest/master/transparent_shadow.png",
                xref="paper", yref="paper",
                x=.5, y=-.17,
                sizex=0.7, sizey=0.7,
                xanchor="center", yanchor="bottom"
            ))

        # update the size and background of the figure
        fig.update_layout(width=1000,
                          height=600,
                          plot_bgcolor='rgba(0, 0, 0, 0)',
                          paper_bgcolor='rgba(0, 0, 0, 0)')

        if self.show:
            fig.show()

        return fig.to_json()

    def money_flow(self, time_period='week'):
        """
        Returns jsonified plotly object which is a line chart depicting net
        income over time for the User.

        Parameters:
            time_period (str): time frame used to define "recent"

        Returns:
            Plotly express object of a line chart in json format
        """
        # subset data down to date and transaction amount
        user_transaction_subset = self.data[["date", "amount_dollars"]]

        # filter down to desired timeframe
        user_transaction_subset = get_last_time_period(
            user_transaction_subset, time_period)

        # prepare data for plotting
        user_transaction_subset.set_index("date", inplace=True)
        user_transaction_subset = user_transaction_subset.sort_index()
        total_each_day = pd.DataFrame(
            user_transaction_subset['amount_dollars'].resample('D').sum())
        total_each_day['amount_flipped'] = total_each_day['amount_dollars']*-1

        # generate the plot figure
        fig = go.Figure(data=go.Scatter(x=total_each_day.index,
                                        y=total_each_day['amount_flipped'],
                                        hovertext=round(
                                            total_each_day['amount_flipped'],
                                            2),
                                        hoverinfo="text",
                                        marker=dict(
                                            color='rgb(192,16,137)',
                                            size=10,
                                            line=dict(
                                                color='Black',
                                                width=2
                                            ))))
        # style the hover labels
        fig.update_layout(width=1000, height=500,
                          hoverlabel=dict(
                              namelength=-1,
                              bgcolor="white",
                              bordercolor='black',
                              font_size=16,
                              font_family="Rockwell",
                          ))

        # add a horizontal line between debt and profit
        fig.add_shape(
            type="line", line_color="salmon", line_width=3, opacity=0.5,
            line_dash="solid", x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y")

        # update title based on time period being viewed
        if time_period == 'all':
            fig.update_layout(
                title={"text": f"Money Flow", "x": 0.5, "y": 0.9})

        else:
            fig.update_layout(title={
                              "text": f"Daily Net Income for the Last {time_period.capitalize()}",
                              "x": 0.5, "y": 0.9})

        # label and style the x and y axis
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Net Income ($)',
            font_size=16,
            template='presentation',
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)')

        if self.show:
            fig.show()

        return fig.to_json()

    def bar_viz(self, time_period='week', category="grandparent_category_name", color_template='Greens_r'):
        """
        Returns jsonified plotly object which is a bar chart of recent
        transactions for the User.

        Parameters:
            time_period (str): time frame used to define "recent"
            category (str): the level of spending category to use
            color_template (str): the plotly sequential color template to use

        Returns:
            Plotly object of a bar chart in json format
        """
        # subset the data using the get_last_time_period method
        subset = get_last_time_period(self.expenses, time_period)

        subset[category] = subset[category].astype(str)

        # group the sum of a categorie's purchases by each day
        subset = subset.groupby([category, 'date']).agg(
            {'amount_dollars': 'sum'})
        subset = subset.reset_index()

        # rename columns for cleaner visualization
        subset.rename({category: 'Category', 'date': 'Date',
                       'amount_dollars': 'Spending ($)'}, axis=1, inplace=True)

        # get list of colors from the plotly's color templates
        color_list = eval('px.colors.sequential.' + color_template)

        # generate bar chart figure
        fig = px.bar(
            subset,
            x='Date',
            y='Spending ($)',
            color='Category',
            color_discrete_sequence=color_list,
            opacity=0.9,
            width=1200,
            height=500,
            template='simple_white'
        )

        # generate title based on time period
        if time_period == 'all':
            fig.update_layout(title={'text': "Daily Spending by Category "})
        else:
            fig.update_layout(title={
                              'text': f"Daily Spending by Category for the Last {time_period.capitalize()}"})

        fig.update_layout(legend=dict(
            yanchor="top",
            y=1,
            xanchor='left',
            x=1
        ))

        # formatting global font size, and title position
        fig.update_layout(font_size=15,
                          plot_bgcolor='rgba(0, 0, 0, 0)',
                          paper_bgcolor='rgba(0, 0, 0, 0)')

        fig.update_layout(barmode='relative',)
        fig.update(layout=dict(title=dict(x=0.45)))

        # create annotations for $ total amounts
        annotations = (subset.groupby(['Date']).sum()).to_dict()
        annotations = dict(annotations['Spending ($)'])

        # add total $ amounts above bars depending on time period
        if time_period == 'week':

            for k, v in annotations.items():
                fig.add_annotation(
                    text=f'    <b>${round(v)}</b>',
                    font_size=16,
                    x=k,
                    y=v,
                    arrowcolor='rgba(0,0,0,0)',
                )

        if time_period == 'month':

            for k, v in annotations.items():
                fig.add_annotation(
                    text=f'    <b>${round(v)}</b>',
                    font_size=10,
                    x=k,
                    y=v,
                    arrowcolor='rgba(0,0,0,0)',
                )

        if self.show:
            fig.show()

        return fig.to_json()

    def predict_budget(self):
        """
        Returns a dictionary of spending predictions for the coming month.

        Uses exponential smoothing to forecast user spending.
        Users with low or insufficient data will trigger warnings that will be
        stored in self.warning_list.
        Small spending categories will be combined into a miscellaneous
        category.
        The names of the combiend categories can be accessed via self.misc.

        Returns:
            Python dictionary of spending predictions.
        """

        # calculate number of transactions in user's expense data
        num_transactions = len(self.expenses)

        # WARNING (Fatal)
        # if user has less than 10 transactions, return None + Warning.
        if num_transactions < 10:
            warning = "Insufficient transaction history. A minimum of 10 transactions is required before generating a budget."
            self.warning_list.append(warning)
            self.warning = 2
            return None

        # WARNING (Non-Fatal)
        # if user has less than 100 transactions, add a warning about poor
        # prediction quality
        elif num_transactions < 100:
            warning = "Your user history contains less than 100 transactions. It is likely this will negatively impact the quality of our budget recommendations."
            self.warning_list.append(warning)
            self.warning = 1

        # calculate how many days does the user's transaction history cover
        transaction_history = (
            max(self.expenses['date']) - min(self.expenses['date'])).days

        # WARNING (Fatal)
        # if transaction history < 2 months of data (60 days), add a warning
        # about poor predictions
        if transaction_history < 60:
            warning = "Your user history does not go back more than 2 months. It is likely this will negatively impact the quality of our budget recommendations."
            self.warning_list.append(warning)
            self.warning = 2
            return None

        # WARNING (Non-Fatal)
        # if transaction history < 6 months of data (180 days), add a warning
        # about poor prediction quality
        elif transaction_history < 180:
            warning = "Your user history does not go back more than 6 months. It is likely this will negatively impact the quality of our budget recommendations."
            self.warning_list.append(warning)
            self.warning = 1

        # get dataframe of average spending per category over last X months
        total_spending_by_month_df = monthly_spending_totals(
            self.expenses, num_months=self.past_months, category=self.cat_column)
        
        print("")
        print(f'total_spending_by_month_df {total_spending_by_month_df.columns}')

        # sets minimum # months which financial activity occured to 10%
        min_frequency = int(self.past_months/10)
        drop_low_frequency_categories(
            total_spending_by_month_df, min_frequency=min_frequency)

        # loop through spending categories and forecast spending for the
        # coming month
        budget = {}
        budget_amount = 0
        for cat in total_spending_by_month_df.columns:
            fit1 = SimpleExpSmoothing(np.asarray(total_spending_by_month_df[cat])).fit(
                smoothing_level=0.6, optimized=False)
            prediction = fit1.forecast(1)[0]
            budget_amount += prediction
            budget[cat] = round(prediction)

        print(f'budget: {budget}')

        # combine small spending categories into a miscellaneous category
        # store the names of the small categories in self.misc so that the
        # budget_modifier() method can access them
        budget, self.misc = dict_trimmer(
            budget, threshold_1=0.05, in_place=False, save=True)

        return budget

    def budget_modifier(self, budget, monthly_savings_goal=50):
        """
        Returns a dictionary of recommended spending for the coming month.

        This method requires predict_budget() to be executed first.
        Uses standard deviation as a measure of how discretionary a spending
        category is.
        Spending categories with higher spending amounts and greater variance
        are treated as "more discretionary".
        Savings goals that are exceedingly large relative to the budget will
        trigger warnings that will be stored in self.warning_list.

        Parameters:
            budget (dictionary): dictionary containing a user's predicted
                spending amounts for the coming month.
                This is the output of predict_budget().
            monthly_savings_goal (int): the amount of money to remove from the
                budgeted amounts

        Returns:
            Python dictionary of spending recommendations.
        """
        # get total budget
        total_budget = 0
        for category in budget:
            total_budget += budget[category]

        # WARNING (Fatal)
        # if savings goal > total budget,
        # set savings goal to 0 and flag warning
        if monthly_savings_goal > total_budget:
            self.warning_list.append(
                f"Your savings goal of {monthly_savings_goal} is larger than your budget of {total_budget}. Please enter a lower savings goal.")
            self.warning = 2
            return None

        # WARNING (Non-Fatal)
        # if savings goal > 30% of total budget,
        # add warning about poor budget recommendation
        if monthly_savings_goal > total_budget * 0.3:
            self.warning_list.append(
                f"Your savings goal of {monthly_savings_goal} is more than 30% of your total budget of {total_budget}. Consider entering a lower savings goal.")
            self.warning = 1

        # get dataframe of average spending per category over the
        # last self.past_months
        total_spending_by_month_df = monthly_spending_totals(
            self.expenses, num_months=self.past_months, category=self.cat_column)

        # create a new misc. category by combining the columns in self.misc
        # (i.e. the columns combined by the trimmer in predict_budget)
        print("")
        print(f'total_spending_by_month_df: {total_spending_by_month_df.columns}')
        print("")
        print(f'self.misc: {self.misc}')
        print("")
        total_spending_by_month_df["Misc."] = total_spending_by_month_df[self.misc].transpose().sum()

        # drop the columns that were combined into the "Misc." column
        total_spending_by_month_df.drop(columns=self.misc, inplace=True)

        # create a dictionary where each key is a standard deviation and each
        # value is the corresponding category
        standard_devs = {}

        # for each category in our budget, calculate the standard deviation
        # for its monthly spending
        for cat in budget:
            std = total_spending_by_month_df[cat].std()
            standard_devs[std] = cat

        # set the number of discretionary categories equal to half the number
        # of total categories rounded up to the nearest whole number
        num_discretionary = ceil(len(budget)/2)

        # get a list of the top std scores
        top_stds = sorted(standard_devs.keys(), reverse=True)[
            0:num_discretionary]

        # get the total budget of all discretionary categories
        total_disc = sum([budget[standard_devs[score]] for score in top_stds])

        # if savings goal > total_disc, then we add more categories to the
        # list until we have enough
        while monthly_savings_goal > total_disc:
            num_discretionary += 1
            top_stds = sorted(standard_devs.keys(), reverse=True)[
                0:num_discretionary]
            total_disc = [budget[standard_devs[score]] for score in top_stds]

        """
        For the top std scores, we find the corresponding budget category, calculate a scaling factor, scale the monthly_savings_goal by that factor, and subtract the result from that category's budget.
        This has the effect of distributing the monly_savings_goal over all discretionary categories with higher weight given to categories that are "more discretionary".
        """
        for score in top_stds:
            category = standard_devs[score]
            scaling_factor = score / sum(top_stds)
            scaled_savings_goal = round(monthly_savings_goal * scaling_factor)
            budget[category] -= scaled_savings_goal

        return budget

    def current_month_spending(self, fixed_categories, current=True, date_cutoff=None):
        """
        Return a user's spending history for their most recent month containing
        spending transactions.
        An int can be passed into the optional date_cutoff parameter to get
        history up to but not including the date specified.

        Parameters:
            fixed_categories (dictionary): dictionary of categories that
                will be explicitly listed in the output regardless of current
                spending amount
            current (bool): determines if "current" refers to the current
                month or the most recent month with user transactions.
                Defaults to the first option.
            date_cutoff (int): if set, this will remove any transactions
                beyond the cutoff date. Primarily used to test/simulate
                user progression.

        Returns:
            Python dictionary of spending recommendations.
        """
        if current:
            # get the current year and month
            cur_year = dt.datetime.now().year
            cur_month = dt.datetime.now().month
        if not current:
            # get the year and month of the most recent transactions
            cur_year = self.expenses['date'].max().year
            cur_month = self.expenses['date'].max().month

        # filter user expenses down to the most recent month
        user_exp = self.expenses.copy()
        cur_month_expenses = user_exp[(user_exp['date'].dt.month == cur_month)
        & (user_exp['date'].dt.year == cur_year)]

        # If a cutoff has been specified, consider only the days in the month
        # up to and including the cutoff
        if date_cutoff:
            cur_month_expenses = cur_month_expenses[
                cur_month_expenses['date'].dt.day <= date_cutoff
                ]

        # get total spending by category
        grouped_expenses = cur_month_expenses.groupby(
            [self.cat_column]).sum()
        grouped_expenses = grouped_expenses.round({'amount_dollars': 2})
        grouped_dict = dict(grouped_expenses['amount_dollars'])

        trimmed_budget = {}
        total_budget = 0
        moved = []
        # loop through current expense categories
        for category in grouped_dict:
            total_budget += grouped_dict[category]

            # if the category is not a fixed (budgeted) category
            if category not in fixed_categories:
                # add it to be empty dict to be trimmed
                trimmed_budget[category] = grouped_dict[category]

                # Track what categories are added. So when the 2
                # dictionaries (fixed and unfixed) are combined, 
                # we know not to count these twice.
                moved.append(category)

        # categories with amounts below this threshold will be combined into a "misc." category
        threshold_1 = total_budget*0.03

        # use trimmer to combine small categories into a misc. category
        dict_trimmer(trimmed_budget, threshold_1=threshold_1, in_place=True)

        # loop through grouped_dict and add it's entries to trimmed_budget.
        for cat in grouped_dict:
            # if the category was aleady added to trimmed budget, pass
            if cat in moved:
                pass
            else:
                # if the category was not moved, but exists in both
                # dictionaries, then add them together
                # this only happens when Misc. is a fixed category and the
                # trimmer generates another Misc. category
                if cat in trimmed_budget:
                    trimmed_budget[cat] += grouped_dict[cat]
                # itherwise, we simply copy the entry into our trimmed_budget
                else:
                    trimmed_budget[cat] = grouped_dict[cat]

        # loop through fixed (budgeted) categories
        for category in fixed_categories:
            # if the user has not spent money in the category this month:
            if category not in trimmed_budget:
                # add it to the grouped_dict with $0 amount to show money
                # hasn't been spent in that category yet
                trimmed_budget[category] = 0

        return trimmed_budget
