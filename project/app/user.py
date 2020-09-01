import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
from datetime import timedelta


def get_last_time_period(transaction_df, time_period='week'):
    """
    Given a dataframe of transactions + dates and a desired timeframe,
    return the dataframe containing only transactions within that time frame.
    If time_period is set to 'all', return the dataframe sorted by date
    """

    # make a copy of the user's expenses dataframe
    transaction_df = transaction_df.copy()
    # sort by date from earlist to latest
    transaction_df = transaction_df.sort_values(by=['date'])
    # grab the lastest date recorded
    latest_time = transaction_df['date'].iloc[-1]
    """
    based on the time period, establish a cutoff in order to subset
    the data
    """
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
    # return the subsetted data

    return subset


def weighted_avg(data):
    """
    Given a dataframe
    Return the datafram with a new column of weighted averages
    """
    categories = data.index
    # get number of timepoints/observations and create weights
    N = data.shape[1]
    weights = [i for i in range(N, 0, -1)]
    averages = []
    # for each categorie, calculate the weighted average and
    # store in the averages list
    for cat in categories:
        cat_data = list(data.loc[cat])
        # replace nan vaalues with 0
        for i in range(len(cat_data)):
            if str(cat_data[i]) == 'nan':
                cat_data[i] = 0
        avg = np.average(cat_data, weights=weights)
        averages.append(avg)

    data['mean'] = averages
    data = data.round()
    return data


def monthly_avg_spending(user_expenses_df, num_months=6, category='grandparent_category_name', weighted=True):
    ticker = 0
    cur_month = user_expenses_df['date'].max().month
    cur_year = user_expenses_df['date'].max().year

    while ticker < num_months:
        # on first iteration
        if ticker == 0:

            if cur_month == 1:
                prev_month = 12
                user_exp_prev = user_expenses_df[(user_expenses_df['date'].dt.month == (
                    prev_month)) & (user_expenses_df['date'].dt.year == (cur_year - 1))]
                prev = user_exp_prev.groupby([category]).sum()
                cur_month = prev_month
                cur_year -= 1

            else:
                prev_month = cur_month - 1
                user_exp_prev = user_expenses_df[(user_expenses_df['date'].dt.month == (
                    prev_month)) & (user_expenses_df['date'].dt.year == cur_year)]
                prev = user_exp_prev.groupby([category]).sum()
                cur_month -= 1

            datestring = f"{prev_month}/{str(cur_year)[2:]}"
            prev.rename(columns={'amount_dollars': datestring}, inplace=True)
            ticker += 1

        else:
            if cur_month == 1:
                prev_month = 12
                other = user_expenses_df[(user_expenses_df['date'].dt.month == (
                    prev_month)) & (user_expenses_df['date'].dt.year == (cur_year - 1))]
                other = other.groupby([category]).sum()
                prev = pd.concat([prev, other], axis=1, sort=True)
                cur_month = prev_month
                cur_year -= 1
            else:
                prev_month = cur_month - 1
                user_exp_prev = user_expenses_df[(user_expenses_df['date'].dt.month == (
                    prev_month)) & (user_expenses_df['date'].dt.year == cur_year)]
                other = user_exp_prev.groupby([category]).sum()
                prev = pd.concat([prev, other], axis=1, sort=True)
                cur_month -= 1

            datestring = f"{prev_month}/{str(cur_year)[2:]}"
            prev.rename(columns={'amount_dollars': datestring}, inplace=True)
            ticker += 1

    if weighted:
        prev = weighted_avg(prev)
    else:
        prev['mean'] = round(prev.mean(axis=1))

    return prev


def trimmer(budget_df, threshold_1=10, threshold_2 = 0, trim_name = 'mean', name = 'Misc.', in_place = True, save = False):
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

    # Use a copy if in_place is set to false
    if in_place == False:
        budget_df = budget_df.copy()

    # If thresholds were set to fractions, then calculate fraction of total average
    # spending and re-assign thresholds
    if 0 < threshold_1 < 1:
        threshold_1 *= budget_df[trim_name].sum()
    if 0 < threshold_2 < 1:
        threshold_2 *= budget_df[trim_name].sum()

    # Get budget categories
    categories = budget_df.index
    
    # Track the eliminated categories and the sum of their means
    trimmed_cats = []
    trimmed_sum = 0

    # For each category, check if the mean is below threshold_1
    # If it is, update trimmed_cats and trimmed_sum then delete the row
    for cat in categories:
        mean = budget_df[trim_name][cat]

        if mean < threshold_1:
            trimmed_sum += mean
            trimmed_cats.append(cat)

            budget_df.drop(index = cat, inplace=True)

    # If trimmed_sum is greater than threshold_2, then we add a new row containing
    # the sum of the means from the deleted rows
    if trimmed_sum > threshold_2:
        new_row = [np.NaN] * (len(budget_df.columns)-1) + [trimmed_sum]
        budget_df.loc[name] = new_row

    # If save = True, then we return both the budget_df and the deleted categories
    if save:
        return (budget_df, trimmed_cats)
    
    return budget_df


class User():
    def __init__(self, id, transactions, name=None, show=False, hole=0.8):
        """
        Constructor for the User class.

        Parameters:
              id (str): user_id
              transactions (dataframe): dataframe consisting of sample transactions
              name (str): user's name. Default is to have no name.
              show (bool): set to True to display graphs after they are generated. Defaults to False
        """
        self.id = id
        self.name = name
        if not self.name:
            self.name = self.id
        self.transactions = transactions
        self.data = self.transactions[self.transactions['plaid_account_id'] == self.id]
        self.expenses = self.data[(self.data['grandparent_category_name'] != 'Transfers') & (
            self.data['amount_dollars'] > 0)]
        self.show = show
        self.past_months = 6
        self.hole = hole

    def get_user_data(self):
        """
        Returns all the user's transactional data in the form of a dataframe.
        """
        return self.data

    def categorical_spending(self, time_period='week', category='grandparent_category_name', color_template = 'Magenta', trim = True):
        """
        Returns jsonified plotly object which is a pie chart of recent transactions for the User.

        Parameters:
              time_period (str): time frame used to define "recent" transactions
              category (str): category type to return
                              (grandparent_category_name (default),
                              parent_category_name,
                              category_name)

        Returns:
              Plotly object of a pie chart in json
        """

        category='grandparent_category_name'
        user_expenses = self.expenses.copy()
        
        # get a list of categories
        cat_count = self.expenses[category].value_counts(normalize=True)

        # filter down to recent transactions
        user_expenses = get_last_time_period(user_expenses, time_period)
        
        # combine transactions by category (required so that each color matches 1 category/label)
        user_expense_grouped = user_expenses.groupby(['grandparent_category_name']).sum()

        # for categories that fall under 2% of transactions, group them into the "Other" category
        trimmer(user_expense_grouped, threshold_1=0.02, trim_name='amount_dollars')

        # get list of colors from the plotly's color templates
        color_list = eval('px.colors.sequential.' + color_template)

        # create pie/donut chart
        fig = go.Figure(data=[go.Pie(labels=user_expense_grouped.index,
                                     values=user_expense_grouped['amount_dollars'],
                                     hole = self.hole,
                                     marker_colors=color_list
                                     )])


        # force percents to be inside donut bars
        fig.update_traces(textposition='inside', textfont_size=14, textinfo="percent")
        
        # add outline to graph objects
        fig.update_traces(marker=dict(colors=self.colors, line=dict(color='#626262', width=1.5)))       
        
        # add title based on current time period being viewed
        if time_period == 'all':     
          fig.update_layout(title={"text" : f"Spending by Category", "x":0.5, "y":0.9}, font_size=16,)

        else:
          fig.update_layout(title={"text" : f"Spending by Category for the Last {time_period.capitalize()}", "x":0.5, "y":0.9}, font_size=16,)

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

        # update the size of the figure
        fig.update_layout(width=1000, height=600,)
        
        if self.show:
            fig.show()
        return fig.to_json()

    def money_flow(self, time_period='week'):
        """
        Returns jsonified plotly object which is a line chart depicting transactions over time for the User.

        Parameters:
              time_period (str): time frame used to define "recent" transactions
        """
        # subset data down to date and transaction amount
        user_transaction_subset = self.data[["date", "amount_dollars"]]

        # filter down to desired timeframe
        user_transaction_subset = get_last_time_period(user_transaction_subset, time_period)

        # prepare data for plotting
        user_transaction_subset.set_index("date", inplace=True)
        user_transaction_subset = user_transaction_subset.sort_index()
        total_each_day = pd.DataFrame(
            user_transaction_subset['amount_dollars'].resample('D').sum())
        total_each_day['amount_flipped'] = total_each_day['amount_dollars'] * -1

        # generate the plot figure
        fig = go.Figure(data=go.Scatter(x=total_each_day.index, 
                                y=total_each_day['amount_flipped'],
                                hovertext=round(total_each_day['amount_flipped'],2),
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
        type="line", line_color="salmon", line_width=3, opacity=0.5, line_dash="solid",
        x0=0, x1=1, xref="paper", y0=0, y1=0, yref="y")

        # update title based on time period being viewed
        if time_period == 'all':
          fig.update_layout(title={"text" : f"Money Flow", "x":0.5, "y":0.9})
                            
        else:

          fig.update_layout(title={"text" : f"Daily Net Income for the Last {time_period.capitalize()}", "x":0.5, "y":0.9})

        # label and style the x and y axis                              
        fig.update_layout(                       
          xaxis_title='Date',
          yaxis_title='Net Income ($)',
          font_size=16,
          template='presentation')
  
        if self.show:
          fig.show()

        return fig.to_json()

        # update title based on time period being viewed
        if time_period == 'all':
            fig.update_layout(
                title={"text": f"Money Flow", "x": 0.5, "y": 0.9},
                xaxis_title='Date',
                yaxis_title='Net Income ($)',
                font_size=16,
                template='presentation')

        else:
            fig.update_layout(
                title={"text": f"Money Flow for the Last {time_period.capitalize()}", "x": 0.5, "y": 0.9},
                xaxis_title='Date',
                yaxis_title='Net Income ($)',
                font_size=16,
                template='presentation')

        if self.show:
            fig.show()

        return fig.to_json()

    def bar_viz(self, time_period='week', category="grandparent_category_name", color_template = 'Greens_r'):
        """
        Uses plotly express
        Returns jsonified plotly object which is a bar chart of recent transactions for the User.

        Parameters:
            time_period (str): time frame used to define "recent" transactions
            category (str): category type to return
                            (grandparent_category_name (default),
                            parent_category_name,
                            category_name)
        Returns:
            Plotly object of a bar chart in json
        """
        # subset the data using the get_last_time_period method
        subset = get_last_time_period(self.expenses, time_period)

        subset[category] = subset[category].astype(str)

        # group the sum of a categorie's purchases by each day rather than by each transaction
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
            fig.update_layout(title={'text': f"Daily Spending by Category for the Last {time_period.capitalize()}"})

        fig.update_layout(legend=dict(
            yanchor="top",
            y=1,
            xanchor='left',
            x=1
        ))

        # formatting global font size, and title position
        fig.update_layout(font_size=15)
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

    def future_budget(self, monthly_savings_goal=50, num_months=6, weighted=True):

        warning = []

        # get dataframe of average spending per category over last 6 months
        avg_spending_by_month_df = monthly_avg_spending(
            self.expenses, num_months=num_months, weighted=weighted)

        # Combine small spending categories into an "other" category
        trimmer(avg_spending_by_month_df, threshold_1=10, threshold_2=25, in_place = True)

        # WARNING
        # If user has less than 10 transactions, return None + Warning.
        if len(self.expenses) < 10:
            warning = "Insufficient transaction history. We require a minimum of 10 transactions before recommending a budget."
            return json.dumps([None, warning])

        # WARNING
        # if savings goal > total budget, set savings goal to 0 and flag warning
        total_budget = avg_spending_by_month_df['mean'].sum()
        if monthly_savings_goal > total_budget:
            warning.append( f"Your savings goal of {monthly_savings_goal} is larger than your budget of {total_budget}. Please enter a lower savings goal.")
            return json.dumps([None, warning])

        # WARNING
        # IF number of transactions < 100, add a warning about poor predictions
        if len(self.transactions) < 100:
            warning.append(f"Your user history contains less than 100 transactions. It is likely this will negatively impact the quality of our budget recommendations.")

        # WARNING
        # IF transaction history < 6 months of data, add a warning about poor predictions
        if (max(self.expenses['date']) - min(self.expenses['date'])).days < 180:
            warning.append("Your user history does not go back more than 6 months. It is likely this will negatively impact the quality of our budget recommendations.")

        # turn into dictionary where key is category and value is average spending
        # . for that category
        avg_cat_spending_dict = dict(avg_spending_by_month_df['mean'])

        # label discretionary columns
        discretionary = ['Food', 'Recreation', 'Shopping', 'Other']

        # add column to df where its True if category is discretionary and False
        # . otherwise
        avg_spending_by_month_df['disc'] = [
            True if x in discretionary else False for x in avg_spending_by_month_df.index.tolist()]

        # get a dictionary of just the discretionary columns and how much was spent
        disc_dict = dict(
            avg_spending_by_month_df[avg_spending_by_month_df['disc'] == True]['mean'])

        # reverse dictionary so key is amount spent and value is category
        disc_dict_reversed = {}
        for k, v in disc_dict.items():
            disc_dict_reversed[v] = k
        
        # WARNING
        # if no discretionary caterories are found, flag warning
        if len(disc_dict_reversed) == 0:
            warning.append(f"Cannot find a discretionary category. This is likely because of insufficient transaction history.")
            return json.dumps([avg_cat_spending_dict, warning])


        # find the key:value pair that shows which discretionary category the user
        # . spent the most money in
        max_cat = max(disc_dict_reversed.items())

        if max_cat[0] < monthly_savings_goal:
            warning = f"Your monthly savings goal of {monthly_savings_goal} is too large compared to your discretionary budget. Please input a smaller savings goal"
            return json.dumps([None, warning])

        # subtract the monthly savings goal from that category
        avg_cat_spending_dict[max_cat[1]] -= monthly_savings_goal

        # If warning list is not empty, add it to the return body
        if len(warning) > 0:
            return json.dumps([avg_cat_spending_dict, warning])

        return avg_cat_spending_dict

    def current_month_spending(self):

        cur_year = self.expenses['date'].max().year
        cur_month = self.expenses['date'].max().month
        user_exp = self.expenses.copy()
        cur_month_expenses = user_exp[(user_exp['date'].dt.month == cur_month) &
                                      (user_exp['date'].dt.year == cur_year)]
        grouped_expenses = cur_month_expenses.groupby(
            ['grandparent_category_name']).sum()
        grouped_expenses = grouped_expenses.round({'amount_dollars': 2})

        grouped_dict = dict(grouped_expenses['amount_dollars'])

        # get dataframe of average spending per category over last 6 months
        avg_spending_by_month_df = monthly_avg_spending(
            self.expenses, num_months=self.past_months)

        # Combine small spending categories into an "other" category
        trimmer(avg_spending_by_month_df, threshold_1=10, threshold_2=25, in_place = True)

        for cat in avg_spending_by_month_df.index:
            if cat not in grouped_dict:
                grouped_dict[cat] = 0

        return grouped_dict
