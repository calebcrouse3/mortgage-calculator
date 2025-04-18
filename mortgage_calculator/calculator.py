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

# Methodology of extra payments
# We compare the cumulative interest saved from extra payments versus the extra payments portfolio
# In otherwords, whats the added net worth from making extra payments?
# Added networth from extra payments is the interest saved - the extra payments.
# Added networth from extra payments portfolio is the extra payments portfolio.

# Methodology of rent versus own comparison.
# What would be your total network worth if you rented instead of buying, assuming all else equal?
# Networth from renting is the cash outlay plus the money saved from renting added to a portfolio - all rent expenses paid.
# Networth from buying is adjusted sale income - all expenses paid.

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
        ownership_exp = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp +
            utility_exp +
            interest_exp
        )
        
        total_exp = ownership_exp + principal_exp + extra_payment_exp

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
            "ownership_exp": ownership_exp,
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
        "total_exp":        ["mean", "sum"],
        "ownership_exp":    "sum",
        "rent_comparison_exp":  ["mean", "sum"],
        "extra_payments_exp":   ["mean", "sum"],
        "loan_balance":         "min", # min if the end of year for loan balance
        "home_value":           "max",
        "rent_comparison_portfolio": "max",
        "extra_payments_portfolio":  "max"
    }

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    # Calculate the "net worth" from owning
    # TODO Mortgage interest deduction, Property tax deduction (up to SALT limits)
    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_min"]
    year_df["realtor_fee"] = year_df["home_value_max"] * inputs.realtor_rate
    year_df["adjusted_cost_basis"] = inputs.home_price + inputs.rehab
    year_df["total_gains"] = year_df["home_value_max"] - year_df["adjusted_cost_basis"]
    year_df["capital_gains_tax"] = year_df["total_gains"] * inputs.capital_gains_tax_rate
    year_df["ownership_exp_cumulative"] = year_df["ownership_exp_sum"].cumsum()
    year_df["net_worth_from_owning"] = year_df["equity"] - year_df["realtor_fee"] - year_df["capital_gains_tax"] - year_df["ownership_exp_cumulative"]

    # Calculate the "net worth" from renting
    year_df["total_exp_cumulative"] = year_df["total_exp_sum"].cumsum()
    year_df["rent_exp_cumulative"] = year_df["rent_comparison_exp_sum"].cumsum()
    year_df["additional_investment"] = year_df["total_exp_cumulative"] - year_df["rent_exp_cumulative"]
    year_df["rent_portfolio_cost_basis"] = year_df["rent_comparison_portfolio_max"] - inputs.cash_outlay - year_df["additional_investment"]
    year_df["capital_gains_tax"] = (year_df["rent_comparison_portfolio_max"] - year_df["rent_portfolio_cost_basis"]) * inputs.capital_gains_tax_rate
    year_df["net_worth_from_renting"] = year_df["rent_comparison_portfolio_max"] - year_df["capital_gains_tax"] - year_df["rent_exp_cumulative"]
    
    year_df["ownership_upside"] = year_df["net_worth_from_owning"] - year_df["net_worth_from_renting"]
    
    return year_df


def get_mortgage_metrics(yearly_df: pd.DataFrame):
    return {
        "Total PMI Paid": yearly_df["pmi_exp_sum"].sum(),
        "Total Taxes Paid": yearly_df["property_tax_exp_sum"].sum(),
        "Total Interest Paid": yearly_df["interest_exp_sum"].sum(),
    }


def get_all_simulation_data(inputs: Inputs):
    monthly_df = get_monthly_sim_df(inputs, extra_payments=True)
    yearly_df = get_yearly_agg_df(inputs, monthly_df)
    mortgage_metrics = get_mortgage_metrics(yearly_df)
    
    results = {
        "yearly_df": yearly_df,
        "mortgage_metrics": mortgage_metrics,
    }
    
    if inputs.mo_extra_payment and inputs.num_extra_payments:
        # Get data with extra payments
        monthly_df_no_extra = get_monthly_sim_df(inputs, extra_payments=False)
        yearly_df_no_extra = get_yearly_agg_df(inputs, monthly_df_no_extra)

        # Compare standard vs extra payments
        comparison_df = pd.merge(
            yearly_df_no_extra["interest_exp_sum"],
            yearly_df[["interest_exp_sum", "extra_payments_portfolio_max", "loan_balance_min", "extra_payments_exp_sum"]]
                .rename(columns={"interest_exp_sum": "interest_exp_sum_with_extra"}),
            on="year",
            how="inner"
        )
        
        # Calculate interest saved from extra payments
        comparison_df["interest_exp_cumulative"] = comparison_df["interest_exp_sum"].cumsum()
        comparison_df["interest_exp_cumulative_with_extra"] = comparison_df["interest_exp_sum_with_extra"].cumsum()
        comparison_df["interest_saved"] = comparison_df["interest_exp_cumulative"] - comparison_df["interest_exp_cumulative_with_extra"]

        # Caculate total return on investment from portfolio
        comparison_df["extra_payments_exp_cumulative"] = comparison_df["extra_payments_exp_sum"].cumsum()
        comparison_df["extra_payments_portfolio_gains"] = comparison_df["extra_payments_portfolio_max"] - comparison_df["extra_payments_exp_cumulative"]

        results["extra_payments_comparison"] = comparison_df[
            [
                "interest_exp_cumulative",
                "interest_exp_cumulative_with_extra",
                "interest_saved",
                "extra_payments_portfolio_max",
                "extra_payments_portfolio_gains",
                "loan_balance_min"
            ]
        ]

    return results
