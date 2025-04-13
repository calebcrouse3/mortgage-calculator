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
    mo_amortized: float = None

    def __post_init__(self):
        self.closing_costs = self.home_price * self.closing_costs_rate
        self.cash_outlay = self.closing_costs + self.down_payment + self.rehab
        self.loan_amount = self.home_price - self.down_payment
        self.mo_amortized = get_amortization_payment(self.loan_amount, self.interest_rate)

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
class SellingInputs:
    realtor_rate: float = 0.06
    capital_gains_tax_rate: float = 0.15

@dataclass
class RentVsOwnInputs:
    # This is the monthly rent you would pay instead of buying the home in consideration
    mo_rent_comparison_exp: int = 1500
    # This is the growth rate an alternative investment with an acceptable risk factor. For example, a bond portfolio.
    rent_surplus_portfolio_growth: float = 0.04

@dataclass
class ExtraPaymentInputs:
    mo_extra_payment: int = 300
    num_extra_payments: int = 12
    # Compare putting money into your home versus investing in an alternative
    extra_payments_portfolio_growth: float = 0.04

@dataclass
class Inputs(
    MortgageInputs,
    ExpensesInputs,
    EconomicFactorsInputs,
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
    rent_comparison_exp = inputs.mo_rent_comparison_exp

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
        principal_exp = inputs.mo_amortized - interest_exp
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
        #      PMI                                                             #
        ########################################################################

        # pay pmi if required
        if not pmi_required:
            pmi_exp = 0

        # update pmi_required, but dont update pmi cost unless its end of year
        pmi_true = get_monthly_pmi(home_value, loan_balance, inputs.pmi_rate, inputs.home_price)
        pmi_required = pmi_true > 0

        ########################################################################
        #      Growth During Month                                             #
        ########################################################################
        
        # Sum of all the expenses for the month
        total_exp = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp +
            utility_exp +
            interest_exp +
            principal_exp +
            extra_payment_exp
        )

        # contribute to portfolio if you saved money from renting
        rent_comparison_portfolio += max(0, total_exp - rent_comparison_exp)

        # contribute any extra payments to portfolio
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
            # Expenses
            "interest_exp": interest_exp,
            "principal_exp": principal_exp,
            "property_tax_exp": property_tax_exp,
            "insurance_exp": insurance_exp,
            "hoa_exp": hoa_exp,
            "maintenance_exp": maintenance_exp,
            "pmi_exp": pmi_exp,
            "utility_exp": utility_exp,
            "total_exp": total_exp,
            # Balances and Values
            "loan_balance": loan_balance,
            "home_value": home_value,
            # Rent Comparison
            "rent_comparison_exp": rent_comparison_exp,
            "rent_comparison_portfolio": rent_comparison_portfolio,
            # Extra Payments
            "extra_payments_exp": extra_payment_exp,
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
            rent_comparison_exp = add_growth(rent_comparison_exp, inputs.yr_rent_increase, 12)

    return pd.DataFrame(data).set_index("index")


def get_yearly_agg_df(inputs: Inputs, sim_df: pd.DataFrame):
    """
    After running the simulation, we want to aggregate the data to a yearly level for easier
    analysis and visualization. This function also calculates some derived metrics for plotting.
    """

    agg_dict = {
        "interest_exp":     ["mean", "sum"],
        "principal_exp":    "mean",
        "property_tax_exp": ["mean", "sum"],
        "insurance_exp":    "mean",
        "hoa_exp":          "mean",
        "maintenance_exp":  "mean",
        "pmi_exp":          ["mean", "sum"],
        "utility_exp":      "mean",
        "total_exp":        "mean",
        "rent_comparison_exp":  "mean",
        "extra_payments_exp":   "mean",
        "loan_balance":         "min", # min if the end of year for loan balance
        "home_value":           "max",
        "rent_comparison_portfolio": "max",
        "extra_payments_portfolio":  "max"
    }

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_min"]

    # Adjusted Cost Basis TODO depreciation
    year_df["adj_cost_basis"] = inputs.home_price + inputs.rehab # - depreciation

    # Sale income is equity - the realtor fee
    year_df["net_proceeds"] = year_df["home_value_max"] * (1 - inputs.realtor_rate)

    # Total capital gains in dollars
    year_df["capital_gains"] = year_df["net_proceeds"] - year_df["adj_cost_basis"]

    return year_df


def get_mortgage_metrics(yearly_df: pd.DataFrame):
    return {
        "Total PMI Paid": yearly_df["pmi_exp_sum"].sum(),
        "Total Taxes Paid": yearly_df["property_tax_exp_sum"].sum(),
        "Total Interest Paid": yearly_df["interest_exp_sum"].sum(),
    }


def get_all_simulation_data(inputs: Inputs, extra_payments: bool = False):
    monthly_df = get_monthly_sim_df(inputs, extra_payments)
    yearly_df = get_yearly_agg_df(inputs, monthly_df)
    mortgage_metrics = get_mortgage_metrics(yearly_df)

    results = {
        "yearly_df": yearly_df,
        "mortgage_metrics": mortgage_metrics,
    }

    return results
