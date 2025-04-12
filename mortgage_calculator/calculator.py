from math import *

import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from mortgage_calculator.utils import *


HEIGHT = 700
WIDTH = 800

ALT_INVESTMENTS = {
    "0.5% (Savings Account)": 0.5,
    "1.1% (10 Year CDs)": 1.1,
    "1.8% (SP500 Dividends)": 1.8,
    "2.5% (Money Market)": 2.5,
    "4.3% (10 Year US Treasury)": 4.3,
    "4.4% (30 Year US Treasury)": 4.4,
    "7.0% (SP500)": 7.0,
}

# e6 = million
# e5 = hundred thousand
# e4 = ten thousand
# e3 = thousand

# int = dollars
# float = rate

# I dont remember what I was going to do with this
# paydown_with_profit = False

@dataclass
class MortgageInputs:
    home_price: int = 300000
    rehab: int = 1000# Cost of repairs or renovations right after buying
    down_payment: int = 50000
    interest_rate: float = 0.065
    closing_costs_rate: float = 0.03 # Calculated as a percentage of home price
    pmi_rate: float = 0.005 # Calculated as a percentage of home price
    
    closing_costs: float = None
    cash_outlay: float = None
    loan_amount: float = None
    monthly_payment: float = None

    def __post_init__(self):
        self.closing_costs = self.home_price * self.closing_costs_rate
        self.cash_outlay = self.closing_costs + self.down_payment + self.rehab
        self.loan_amount = self.home_price - self.down_payment
        self.monthly_payment = get_amortization_payment(self.loan_amount, self.interest_rate)

@dataclass
class ExpensesInputs:
    yr_property_tax_rate: float = 0.01
    yr_insurance_rate: float = 0.0035
    mo_hoa_fees: int = 0
    mo_utility: int = 200
    yr_maintenance: float = 0.015

@dataclass
class EconomicFactorsInputs:
    yr_home_appreciation: float = 0.03
    yr_inflation_rate: float = 0.03
    yr_rent_increase: float = 0.03
    
@dataclass
class RentalIncomeInputs:
    mo_rent_income: int = 0
    mo_other_income: int = 0
    vacancy_rate: float = 0.05
    management_rate: float = 0.1
    income_tax_rate: float = 0.25

@dataclass
class SellingInputs:
    realtor_rate: float = 0.06
    capital_gains_tax_rate: float = 0.15

@dataclass
class RentVsOwnInputs:
    # This is the monthly rent you would pay instead of buying the home in consideration
    rent_exp: int = 1500
    # This is the growth rate an alternative investment with an acceptable risk factor. For example, a bond portfolio.
    rent_surplus_portfolio_growth: float = 0.04

@dataclass
class ExtraPaymentInputs:
    mo_extra_payment: int = 300
    num_extra_payments: int = 12
    extra_payments_portfolio_growth: float = 0.04

@dataclass
class Inputs(
    MortgageInputs,
    ExpensesInputs,
    EconomicFactorsInputs,
    RentalIncomeInputs,
    SellingInputs,
    RentVsOwnInputs,
    ExtraPaymentInputs
):
    def to_dict(self) -> dict:
        """Returns all data within the inputs as a dictionary."""
        return asdict(self)


def get_monthly_sim_df(inputs: Inputs, extra_payments: bool = False):
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.

    Extra payments will apply extra payments to the principle of the loan and also add the extra payment
    to the extra payments portfolio.

    PMI is a little tricky to follow because it can be cancelled anytime based on the price of PMI 
    returned by the function but the price paid is updated once a year.
    pmi_true:     holds the value of PMI if it was recalculated
    pmi_exp:      holds the actual PMI paid and is updated yearly
    pmi_required: is not required if the true_pmi <= 0 and will cancel the pmi_exp

    The simulation will track additional portfolios in parallel for comparison whose value 
    do not effect the mortgage and expenses itself.
    """

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_exp = get_monthly_pmi(
        inputs.home_price, 
        inputs.loan_amount, 
        inputs.pmi_rate, 
        inputs.home_price
    )
    property_tax_exp = inputs.home_price * inputs.yr_property_tax_rate / 12
    insurance_exp = inputs.home_price * inputs.yr_insurance_rate / 12
    maintenance_exp = inputs.home_price * inputs.yr_maintenance / 12
    hoa_exp = inputs.mo_hoa_fees
    utility_exp = inputs.mo_utility
    rent_income = inputs.mo_rent_income
    other_income = inputs.mo_other_income
    management_exp = inputs.management_rate * rent_income
    rent_exp = inputs.rent_exp

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    loan_balance = inputs.loan_amount
    home_value = inputs.home_price
    pmi_required = pmi_exp > 0

    # Stock portfolio comparisons
    rent_comparison_portfolio = inputs.cash_outlay # portfolio funded with money saved from renting
    extra_payments_portfolio = 0 # portfolio funded with extra payments


    data = []
    for month in np.arange(12 * 30):

        ########################################################################
        #      Principle and Interest                                          #
        ########################################################################

        interest_exp = loan_balance * inputs.interest_rate / 12
        principal_exp = inputs.monthly_payment - interest_exp
        extra_payment_exp = 0

        # extra payments are the only time we might need to adjust principle exp
        if extra_payments:
            if principal_exp >= loan_balance:
                principal_exp = loan_balance
            elif month < inputs.num_extra_payments:
                extra_payment_exp = min(loan_balance - principal_exp, inputs.mo_extra_payment)

        loan_balance -= principal_exp
        loan_balance -= extra_payment_exp

        ########################################################################
        #      Expenses                                                        #
        ########################################################################

        # pay pmi if required
        if not pmi_required:
            pmi_exp = 0

        op_exp = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp +
            utility_exp +
            management_exp
        )

        total_exp = op_exp + interest_exp + principal_exp + extra_payment_exp
        total_income = rent_income + other_income
        adj_total_income = total_income * (1 - inputs.vacancy_rate)
        noi = adj_total_income - op_exp
        niaf = adj_total_income - total_exp

        # apply income tax to profits
        if niaf > 0:
            niaf *= (1 - inputs.income_tax_rate)

        # update pmi_required, but dont update pmi cost unless its end of year
        pmi_true = get_monthly_pmi(home_value, loan_balance, inputs.pmi_rate, inputs.home_price)
        pmi_required = pmi_true > 0

        ########################################################################
        #      Growth During Month                                             #
        ########################################################################

        # contribute to portfolio if money saved from renting
        if total_exp > rent_exp:
            rent_comparison_portfolio += total_exp - rent_exp

        # contribute any extra payments to portfolio
        if extra_payment_exp > 0:
            extra_payments_portfolio += extra_payment_exp

        home_value = add_growth(home_value, inputs.yr_home_appreciation, months=1)
        rent_comparison_portfolio = add_growth(
            rent_comparison_portfolio, 
            inputs.rent_surplus_portfolio_growth, 
            months=1
        )
        extra_payments_portfolio = add_growth(
            extra_payments_portfolio, 
            inputs.extra_payments_portfolio_growth, 
            months=1
        )

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # Costs, payments, revenue. Monthly Totals.
            "interest_exp": interest_exp,
            "principal_exp": principal_exp,
            "property_tax_exp": property_tax_exp,
            "insurance_exp": insurance_exp,
            "hoa_exp": hoa_exp,
            "maintenance_exp": maintenance_exp,
            "pmi_exp": pmi_exp,
            "utility_exp": utility_exp,
            "management_exp": management_exp,
            "op_exp": op_exp,
            "total_exp": total_exp,
            "rent_income": rent_income,
            "other_income": other_income,
            "total_income": total_income,
            "adj_total_income": adj_total_income,
            "noi": noi,
            "niaf": niaf,
            "rent_exp": rent_exp,
            "extra_payment_exp": extra_payment_exp,
            # Balances and values. End of month.
            "loan_balance": loan_balance,
            "home_value": home_value,
            "rent_comparison_portfolio": rent_comparison_portfolio,
            "extra_payments_portfolio": extra_payments_portfolio
        }
        data.append(month_data)

        ########################################################################
        #      Growth End of Year - Applies to next month values               #
        ########################################################################

        if (month + 1) % 12 == 0 and month > 0:
            property_tax_exp = home_value * inputs.yr_property_tax_rate / 12
            insurance_exp = home_value * inputs.yr_insurance_rate / 12
            hoa_exp = add_growth(hoa_exp, inputs.yr_inflation_rate, 12)
            utility_exp = add_growth(utility_exp, inputs.yr_inflation_rate, 12)
            maintenance_exp = home_value * inputs.yr_maintenance / 12
            pmi_exp = pmi_true
            rent_income = add_growth(rent_income, inputs.yr_rent_increase, 12)
            other_income = add_growth(other_income, inputs.yr_rent_increase, 12)
            management_exp = inputs.management_rate * rent_income
            rent_exp = add_growth(rent_exp, inputs.yr_rent_increase, 12)

    return pd.DataFrame(data).set_index("index")


def get_yearly_agg_df(inputs: Inputs, sim_df: pd.DataFrame):
    """
    After running the simulation, we want to aggregate the data to a yearly level for easier
    analysis and visualization. This function also calculates some derived metrics for plotting.
    """

    # List of columns for sum and mean aggregations
    sum_mean_cols = [
            "interest_exp", "principal_exp", "property_tax_exp", "insurance_exp",
            "hoa_exp", "maintenance_exp", "pmi_exp", "utility_exp", "management_exp",
            "op_exp", "total_exp", "rent_income", "other_income", "total_income",
            "adj_total_income", "noi", "niaf", "rent_exp", "extra_payment_exp"
    ]

    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}

    agg_dict.update({
        "loan_balance": "min", # min if the end of year for loan balance
        "home_value": "max",
        "rent_comparison_portfolio": "max",
        "extra_payments_portfolio": "max"
    })

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    def rename_columns(df):
        # remove sum from columns.
        # Value is implied total for the year,
        # mean value is implied for monthly.
        # also remove min and max from loan balance and home value,
        # its implied that these columns are values at the end of the year
        new_columns = {}
        for col in df.columns:
            if col.endswith('_sum') or col.endswith('_max') or col.endswith('_min'):
                new_columns[col] = col[:-4]
            elif col.endswith('_mean'):
                new_columns[col] = col[:-5] + '_mo'
        df.rename(columns=new_columns, inplace=True)

    rename_columns(year_df)

    cumsum_cols = [
        "niaf",
        "rent_exp",
        "interest_exp",
        "principal_exp",
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # VALIDATED: this is the amount of ownership of the home you have at the end of the year
    year_df["equity"] = year_df["home_value"] - year_df["loan_balance"]
    # VALIDATED: this gives the total income from selling the home in a particular year which factors in seling costs
    year_df["sale_income"] = year_df["equity"] - (year_df["home_value"] * inputs.realtor_rate)
    
    # these need to be understood and validated
    year_df["capital_gains"] = year_df["sale_income"] + year_df["cum_principal_exp"] - inputs.home_price - inputs.down_payment
    year_df["return"] = year_df["capital_gains"] + year_df["cum_niaf"] - inputs.closing_costs - inputs.rehab


    # VALIDATED: this gives the total return for the time period up to a particular year if the home is sold
    year_df["total_return"] = year_df["cum_niaf"] + year_df["sale_income"] - inputs.cash_outlay
    # ALMOST VALIDATED: This is the total net value of assets (cash and property) at the end of the year. 
    # Not sure if using sale income or equity is better. What does "net worth" imply?. 
    # Depends on if you still own the home or not I guess.
    year_df["net_worth_post_sale"] = year_df["cum_niaf"] + year_df["sale_income"] - inputs.rehab - inputs.closing_costs
    
    
    # ALMOST VALIDATED: this gives the tota rate of return for the time period up to a particular year if the home is sold
    year_df["roi"] = year_df["total_return"] / inputs.cash_outlay
    # VALIDATED: Annualized yearly ROI for the time period up to a particular year if the home is sold at the end of that year.
    # Version of the CAGR formula. Also have to add 1 to index to make it number of years passed.
    year_df["annualized_roi"] = (1 + year_df["roi"]) ** (1 / (year_df.index + 1)) - 1
    # VALIDATED: this gives the coc return in a particular year ignoring home sale income
    year_df["annualized_coc_roi"] = year_df["niaf"] / inputs.cash_outlay
    # VALIDATE: Return on equity is the annual return divided by the equity in the home
    # This probably needs to be altered to reflect the equity at the beginning of the year, or even use the sale income at the beginning of the year
    # And the return should probably also include appreciation of the home
    #year_df["start_equity"] = year_df["equity"].shift(1)
    year_df["start_sale_income"] = year_df["sale_income"].shift(1)
    #year_df["start_sale_income"].iloc[0] = ss.down_payment.val * (1 - ss.realtor_rate.val)
    year_df["annual_roe"] = (year_df["sale_income"] - year_df["start_sale_income"] + year_df["niaf"]) / year_df["start_sale_income"]
    
    
    # parallel simulations. Need to get Net worth of these simulations
    year_df["renting_net_worth"] = year_df["rent_comparison_portfolio"] * (1 - inputs.capital_gains_tax_rate) - year_df["cum_rent_exp"]
    year_df["extra_payments_portfolio"] = year_df["extra_payments_portfolio"] * (1 - inputs.capital_gains_tax_rate)

    return year_df


def get_mortgage_metrics(inputs: Inputs, yearly_df: pd.DataFrame):
    return {
        "Down Payment": inputs.down_payment,
        "Rehab": inputs.rehab,
        "Closing Costs": inputs.closing_costs,
        "Cash Outlay": inputs.cash_outlay,
        "Loan Amount": inputs.loan_amount,
        "Total PMI Paid": yearly_df["pmi_exp"].sum(),
        "Total Taxes Paid": yearly_df["property_tax_exp"].sum(),
        "Total Interest Paid": yearly_df["interest_exp"].sum(),
    }


def get_investment_metrics(inputs: Inputs, yearly_df: pd.DataFrame):
    # opr_metrics. Monthly income / cash_outlay
    opr = yearly_df.loc[0, "rent_income_mo"] / inputs.home_price

    GRM = 0 
    if yearly_df.loc[0, "rent_income"] > 0:
        GRM = int(yearly_df.loc[0, "home_value"] / yearly_df.loc[0, "rent_income"])

    return  {
        "Gross Rental Multiplier": GRM,
        "Cap Rate": yearly_df.loc[0, "noi"] / inputs.home_price,
        "First Mo. Cash Flow": yearly_df.loc[0, "niaf_mo"],
        "5 Year Annualized ROI": yearly_df.loc[4, "annualized_roi"],
        "1% Rule": f"Yes {opr}" if opr >= 0.01 else f"No {opr}",
    }


def get_all_simulation_data(inputs: Inputs, extra_payments: bool = False):
    monthly_df = get_monthly_sim_df(inputs, extra_payments)
    yearly_df = get_yearly_agg_df(inputs, monthly_df)

    mortgage_metrics = get_mortgage_metrics(inputs, yearly_df)
    investment_metrics = get_investment_metrics(inputs, yearly_df)

    results = {
        "yearly_df": yearly_df,
        "mortgage_metrics": mortgage_metrics,
        "investment_metrics": investment_metrics,
    }

    return results


def calculate_and_display():

    results = get_all_simulation_data(include_metrics=True)
    yearly_df = results["yearly_df"]

    # Extra Payments stuff could be handled better...
    
    extra_payments_df = get_all_simulation_data(extra_payments=True)["yearly_df"]
    append_cols = ["net_worth_post_sale", "extra_payments_portfolio", "loan_balance", "extra_payment_exp"]
    merged_df = merge_simulations(yearly_df, extra_payments_df, append_cols, "ep")

    # add regular profit with extra payment portfolio from extra_payments_df which has been joined
    merged_df["portfolio_nw"] = merged_df["net_worth_post_sale"] + merged_df["ep_extra_payments_portfolio"]

    # get delta for both simluations against just regulat profit
    merged_df["portfolio_nw_delta"] = merged_df["portfolio_nw"] - merged_df["net_worth_post_sale"]
    merged_df["ep_nw_delta"] = merged_df["ep_net_worth_post_sale"] - merged_df["net_worth_post_sale"]

    # remove any rows after the first row with a loan balance of 0
    zero_index = merged_df[merged_df["ep_loan_balance"] == 0].index[0]

    merged_df = merged_df.loc[:zero_index]

    crossover = min_crossover(merged_df["ep_nw_delta"].values, merged_df["portfolio_nw_delta"].values)
    df_len = len(merged_df)
    total_extra_payments = merged_df["ep_extra_payment_exp"].sum()

    extra_payments_metrics = {
        "Reduced Payoff Time": f"{30 - df_len} Years",
        "Total Extra Payment": total_extra_payments,
        "Total Interest Savings": merged_df.loc[zero_index, "ep_nw_delta"]
    }
    
    # Figures from extra_payments_df
    cols = ["portfolio_nw_delta", "ep_nw_delta"]
    names= ["Contribute to Stocks", "Pay Down Loan"]
    title = "Added Net Worth From Extra Payments"
              
    if crossover == -1:
        print("Over the long run, you would probably have more money if you had invested in the stock market.")
    elif crossover >= 0:
        print(f"Making these extra payments is a smart idea if plan on living in this house for at least {crossover} years.")
