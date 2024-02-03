"""This code doesnt run but saves the logic for the rental comparison simulator"""



def mortgage_inputs():
    st.markdown("### Mortgage")
    populate_columns([
        lambda: dollar_input("Home Price", ss.home_price.key,
            help="The price of the home you are considering purchasing."
        ),
    ], 2)
    populate_columns([
        lambda: dollar_input("Down Payment", ss.down_payment.key, 
            help="""The amount of cash you have to put towards the upfront costs of buying a home. 
            Closing costs will be subtracted from this value and the remainder is the effective 
            down payment."""
        ),
        lambda: rate_input("Interest", ss.interest_rate.key, 
            help="""The interest rate on your mortgage. Each month, this percentage is multiplied 
            by the remaining loan balance to calculate the interest payment."""
        ),
    ], 2)
    populate_columns([
        lambda: rate_input("Home Value Growth", ss.yr_home_appreciation.key, asterisk=False, 
            help="""The yearly increase in the value of your home. As your home increases in value, 
            you'll have to pay more in property taxes and insurance. This value is updated whenever
            you select a new region and corresponds to the median yearly home value increase over 
            the past 10 years in that region"""
        ),
        lambda: rate_input("Property Tax", ss.yr_property_tax_rate.key, asterisk=False, 
            help="""This is the tax rate on your property. Property tax rates are set by the state 
            government. This rate is multiplied by the value of the home to get the total taxes paid 
            each year. This value is updated whenever you select a new region and corresponds to the 
            median property tax rate in the state in which this region is located."""
        ),
    ], 2)
    populate_columns([
        lambda: dollar_input("HOA Fees", ss.mo_hoa_fees.key,
            help="""If your home is part of a homeowners association, you will have to pay monthly
            HOA fees. This value is updated each year based on the inflation rate."""
        ),
            lambda: rate_input("Insurance Rate", ss.yr_insurance_rate.key,
            help="""This is the yearly cost of homeowners insurance. This rate is multiplied by the
            value of the home to get the total insurance paid each year. Insurance rates can vary
            based on the location of the home and the type of insurance coverage.""",
        ),
    ], 2)


def other_inputs():
    with st.expander("Mortgage+", expanded=False):
        st.write("The defaults here will probably work for most people")
        populate_columns([
            lambda: rate_input("Closing Costs", ss.closing_costs_rate.key, 
                help="""These are the additional upfront cost of buying a home through a lender. 
                Its often calculated as a percentage of the purchase price of the home. The closing costs
                will be subracted from your down payment to calculate the effective down payment."""
                ),
            lambda: rate_input("PMI Rate", ss.pmi_rate.key, 
                help="""PMI is an additional monthly cost that is required if your down payment is less
                than 20% of the purchase price of the home. This rate is multiplied by the value of the
                home to get the total PMI paid each year. PMI can be cancelled once you have 20% equity in the home
                which can occur from paying down the principle or from the value of the home increasing."""
                ),
        ], 2)
        populate_columns([
            lambda: rate_input("Inflation Rate", ss.yr_inflation_rate.key,
                help="""This is the yearly inflation rate which measure how the cost of goods goes 
                up. This rate is used to update the value of your monthly maintenance and HOA fees 
                each year."""
            ),
            lambda: dollar_input("Monthly Maintenance", ss.mo_maintenance.key,
                help="""Owning a home requires maintenance and upkeep. This is the monthly cost of
                maintaining your home. This value is updated each year based on the inflation rate."""
            ),     
        ], 2)


def extra_mortgage_payment_inputs():
    with st.expander("Extra Payments", expanded=False):
        st.write("Extra payments can help you pay off your loan faster and reduce the total amount of interest you pay over the life of the loan.")
        populate_columns([
            lambda: dollar_input("Extra Monthly Payments", ss.mo_extra_payment.key,
            help="""This is the amount of extra money you will pay towards the principle of your loan
            each month. This can help you pay off your loan faster and reduce the total amount of
            interest you pay over the life of the loan."""                     
            ),
            lambda: st.number_input("Number of Payments", min_value=0, max_value=int(1e4), key=ss.num_extra_payments.key,
            help="""This is the number of months you will pay extra payments towards the principle of
            your loan. After this number of months, you will stop paying extra payments and only pay
            the normal monthly payment."""
            ),
        ], 2)


def rent_income_inputs():
    with st.expander("Rental Income", expanded=False):
        st.write("You can rent out all or a portion of your home to offset the cost of homeownership or make some profit.")
        populate_columns([
            lambda: dollar_input("Monthly Rental Income", ss.mo_rent_income.key,
                help="""This is the monthly cost of renting a home. This value is updated each year
                based on the yearly rent increase rate."""      
            ),
            lambda: rate_input("Yearly Rent Increase", ss.yr_rent_increase.key,
                help="""This is the yearly increase in the cost of rent. This value is used to update
                the monthly rent each year."""
            ),
        ], 2)


def calculate():
    populate_columns([
        lambda: st.button("Reset Values", on_click=ss.clear, help="Reset all inputs to their default values."),
        lambda: st.button("Calculate", help="Run the simulation with the current inputs."),
    ], 2)


def hide_text_input():
    populate_columns([
        lambda: st.checkbox("Hide All Text Blobs", key=ss.hide_text.key),
    ], 2)



def renting_comparison_inputs():
    #with st.expander("Renting Comparison Inputs", expanded=False):
        populate_columns([
            lambda: dollar_input("Monthly Rent", ss.mo_rent_cost.key,
                help="""This is the monthly cost of renting a home. This value is updated each year
                based on the yearly rent increase rate."""      
            ),
            # lambda: rate_input("Yearly Rent Increase", ss.rent_increase,
            #     help="""This is the yearly increase in the cost of rent. This value is used to update
            #     the monthly rent each year."""
            # ),
            # lambda: rate_input("Stock Return Rate", ss.stock_growth_rate,
            #     help="""This is the yearly return rate of the stock market. This value is used to
            #     calculate the growth of your portfolio over time."""       
            # )
        ], 3)


# CONSTANTS
CLOSING_COSTS = ss.home_price.val * ss.closing_costs_rate.val
EFFECTIVE_DOWN_PAYMENT = max(ss.down_payment.val - CLOSING_COSTS, 0)
LOAN_AMOUNT = ss.home_price.val - EFFECTIVE_DOWN_PAYMENT
MONTHLY_PAYMENT = get_monthly_payment_amount(LOAN_AMOUNT, ss.interest_rate.val)

def run_simulation():
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.
    """

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_cost = get_monthly_pmi(ss.home_price.val, LOAN_AMOUNT, ss.pmi_rate.val, ss.home_price.val)
    property_tax_cost = ss.home_price.val * ss.yr_property_tax_rate.val / 12
    insurance_cost = ss.home_price.val * ss.yr_insurance_rate.val / 12
    hoa_cost = ss.mo_hoa_fees.val
    rent_cost = ss.mo_rent_cost.val
    portfolio_value = ss.down_payment.val
    rent_income = ss.mo_rent_income.val

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    maintenance_cost = ss.mo_maintenance.val
    loan_balance = LOAN_AMOUNT
    home_value = ss.home_price.val
    pmi_required = pmi_cost > 0
    extra_payment = ss.mo_extra_payment.val


    data = []
    for month in np.arange(12 * 30):

        interest_paid = loan_balance * ss.interest_rate.val / 12
        
        # cant pay more principal than loan balance
        principal_paid = MONTHLY_PAYMENT - interest_paid
        if principal_paid >= loan_balance:
            principal_paid = loan_balance

        loan_balance -= principal_paid

        # stop paying extra payments after allotted number of payments
        # cant pay more extra payments than loan balance
        if month > ss.num_extra_payments.val - 1:
            extra_payment = 0
        elif extra_payment >= loan_balance:
                extra_payment = loan_balance

        loan_balance -= extra_payment

        # pay pmi if required
        pmi_paid = 0
        if pmi_required:
            pmi_paid = pmi_cost

        # update portfolio value
        contribution = (
            interest_paid +
            principal_paid +
            extra_payment +
            property_tax_cost +
            insurance_cost +
            hoa_cost +
            maintenance_cost +
            pmi_paid
        ) - rent_cost

        contribution = max(contribution, 0)
        portfolio_value = add_growth(
            portfolio_value, 
            ss.yr_stock_appreciation.val, 
            months=1, 
            monthly_contribution=contribution
        )

        # update home value
        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)

        # update monthly maintenance costs
        maintenance_cost = add_growth(maintenance_cost, ss.yr_inflation_rate.val, months=1)

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = true_pmi > 0

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_cost = home_value * ss.yr_property_tax_rate.val / 12
            insurance_cost = home_value * ss.yr_insurance_rate.val / 12
            hoa_cost = add_growth(hoa_cost, ss.yr_inflation_rate.val, 12)
            rent_cost = add_growth(rent_cost, ss.yr_rent_increase.val, 12)
            pmi_cost = true_pmi
            rent_income = add_growth(rent_income, ss.yr_rent_increase.val, 12)

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # costs and payments
            "interest": interest_paid,
            "principal": principal_paid,
            "extra_payment": extra_payment,
            "property_tax": property_tax_cost,
            "insurance": insurance_cost,
            "hoa": hoa_cost,
            "maintenance": maintenance_cost,
            "pmi": pmi_paid,
            "rent": rent_cost,
            # balances and values
            "loan_balance": loan_balance,
            "home_value": home_value,
            "portfolio_value": portfolio_value,
            # house hacking / rental income
            "rent_income": rent_income,
        }
        data.append(month_data)
    return pd.DataFrame(data).set_index("index")


def post_process_sim_df(sim_df):
    """
    After running the simulation, we want to aggregate the data to a yearly level for easier
    analysis and visualization. This function also calculates some derived metrics related to 
    renting comparisons and rental income.
    """

    # add total and misc columns
    sim_df["total"] = sim_df[[
        "interest", "principal", "pmi", "insurance", 
        "property_tax", "hoa", "maintenance", "extra_payment"
    ]].sum(axis=1)

    sim_df["misc"] = sim_df[[
        "pmi", "insurance", "property_tax", 
        "hoa", "maintenance"
    ]].sum(axis=1)

    # List of columns for sum and mean aggregations
    sum_mean_cols = [
        "pmi", "insurance", "property_tax", "hoa", 
        "maintenance", "interest", "principal", 
        "misc", "total", "rent", "extra_payment",
        "rent_income"
    ]

    # Columns for max aggregation
    max_cols = ["home_value", "loan_balance", "portfolio_value"]

    # Generate aggregation dictionary
    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}
    agg_dict.update({col: 'max' for col in max_cols})

    # Group and aggregate
    year_df = sim_df.groupby("year").agg(agg_dict)

    # Renaming columns for clarity
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    # total minus rental income
    year_df["total_mean_hh"] = year_df["total_mean"] - year_df["rent_income_mean"]

    # cumulative cols for principal, interest, total, misc
    cols_to_cumsum = ["total_sum", "interest_sum", "principal_sum", "extra_payment_sum", "misc_sum", "rent_sum", "rent_income_sum"]

    for col in cols_to_cumsum:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # Define rates and costs upfront for clarity
    closing_costs = ss.closing_costs_rate.val * ss.home_price.val

    # Calculate equity
    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_max"]

    # money you pay that doesnt go towards equity
    year_df["home_costs"] = closing_costs + year_df["cum_interest_sum"] + year_df["cum_misc_sum"]
    year_df["equity_less_costs"] = year_df["equity"] - year_df["home_costs"]
    year_df["equity_less_costs_hh"] = year_df["equity"] - year_df["home_costs"] +  year_df["cum_rent_income_sum"]
    year_df["stocks_less_renting"] = year_df["portfolio_value_max"] - year_df["cum_rent_sum"]

    return year_df



    renting_metrics = {
        "Years until Homeownership is Cheaper": min_crossover(yearly_df["equity_less_costs_hh"], yearly_df["stocks_less_renting"]) + 1,
        "Homeownership upside 5 Years": format_currency(yearly_df["equity_less_costs_hh"].iloc[4] - yearly_df["stocks_less_renting"].iloc[4]),
        "Homeownership upside 10 Years":format_currency( yearly_df["equity_less_costs_hh"].iloc[9] - yearly_df["stocks_less_renting"].iloc[9]),
    }


    ########################################################################
    #      Renting                                                         #
    ########################################################################

    with tab_rent:
        # TODO two lines for profit and profit with rent?
    
        if not ss.hide_text.val:
            get_rental_comparison_intro(ss.yr_rent_increase.val)

        renting_comparison_inputs()
        # st.write(renting_metrics)

        cols=["equity_less_costs_hh", "stocks_less_renting"]
        names=["Renting and Stocks"]

        if ss.mo_rent_income.val > 0:
            names = ["Home with Rental Income"] + names
        else:
            names = ["Home"] + names

        colors = ['#2ca02c', 'purple']

        fig = go.Figure()

        for idx, (col, name) in enumerate(zip(cols, names)):
            fig.add_trace(go.Scatter(
                x=yearly_df.index + 1, 
                y=yearly_df[col], 
                mode='lines', 
                name=name,
                hoverinfo='y',
                hovertemplate='$%{y:,.0f}',
                line=dict(width=4, color=colors[idx]),  # Use the color corresponding to the current index
            ))

        # Update layout
        fig.update_layout(
            title="Renting vs. Homeownership Profit",
            xaxis=dict(
                title='Year',
            ),
            yaxis=dict(
                title='Value at End of Year',
                tickformat='$,.0f'
            ),
            height=700,
            hovermode='x'
        )

        # Display the figure
        fig_display(fig)




def get_metrics(yearly_df):

    default_interest_paid = get_total_interest_paid(LOAN_AMOUNT, ss.interest_rate.val)
    actual_interest_paid = sum(yearly_df['interest_sum'])
    

    # find first year where equity minus costs is higher than previous year
    def year_of_uptrend(values):
        for i in range(len(values) - 1):
            if values[i + 1] > values[i]:
                return i + 1
        return 30
            

    # Function that tells you at what index x is greater than y
    def min_crossover(x, y):
        for i in range(len(x)):
            if x[i] > y[i]:
                return i
        return 30
    

    def year_of_profit(init_equity, profit_col):
        for i in range(len(profit_col)):
            if profit_col[i] > init_equity:
                return i
        return 30
    
    summary_metrics = {
        "Loan Amount": format_currency(LOAN_AMOUNT),
        "Closing Costs": format_currency(CLOSING_COSTS),
        "Effective Down Payments": format_currency(EFFECTIVE_DOWN_PAYMENT),
        "Total Paid": format_currency(sum(yearly_df['total_sum'])),
        "Principal Paid": format_currency(sum(yearly_df['principal_sum'])),
        "Interest Paid": format_currency(actual_interest_paid),
        "Taxes Paid": format_currency(sum(yearly_df['property_tax_sum'])),
        "Other Expenses Paid": format_currency(sum(yearly_df['misc_sum'])),
        "PMI Paid": format_currency(sum(yearly_df['pmi_sum'])),
        "Extra Payments": format_currency(sum(yearly_df['extra_payment_sum'])),
        "Interest Saved": format_currency(max(0, default_interest_paid - actual_interest_paid)),
        "Rental Income": format_currency(sum(yearly_df['rent_income_sum'])),
    }

    home_value_metrics = {
        "Years until Profitable": "TODO", # int(year_of_uptrend(yearly_df["equity_less_costs_hh"])),
        "Years until Profitable with Rent": "TODO",
        "Increased Equity 10 Years": format_currency(yearly_df["equity"].iloc[10] -  yearly_df["equity"].iloc[10]),
    }

    return summary_metrics, home_value_metrics
