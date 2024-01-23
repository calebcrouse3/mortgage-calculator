import streamlit as st
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from math import *
from utils import *
from utils_finance import *
from st_text import *
from dataclasses import dataclass


def rate_input(label, default, min_value=0.0, max_value=99.0, step=0.1):
    return st.number_input(label=f"{label} (%)", min_value=min_value, max_value=max_value, value=default, step=step) / 100


def dollar_input(label, default, min_value=0, max_value=1e8):
    # function that will calculate the step input based on the default value where the step is
    # 1eN where N is one less than the number of digits in the default value
    step=10
    if default > 100:
        step = int(10 ** (floor(log10(default)) - 1))
    return st.number_input(f"{label} ($)", min_value=min_value, max_value=int(max_value), value=int(default), step=step)

    
@dataclass
class MortgageInputs:
    city: str
    init_home_value: float
    down_payment: float
    interest_rate: float
    yearly_home_value_growth: float
    property_tax_rate: float


@dataclass
class OtherFactorsInputs:
    closing_costs_rate: float
    pmi_rate: float
    insurance_rate: float
    init_hoa_fees: float
    init_monthly_maintenance: float
    inflation_rate: float


@dataclass
class HomeSellingCostsInputs:
    realtor_rate: float
    sell_closing_costs_rate: float
    additional_selling_costs: float

    
@dataclass
class RentStockInputs:
    init_rent: float
    yearly_rent_increase: float
    stock_market_growth_rate: float
    stock_tax_rate: float


def get_columns(n=6):
    return st.columns(n)


def populate_columns(values, dataclass):
    output_vals = []
    columns = get_columns()
    for col, value_func in zip(columns[:len(values)], values):
        with col:
            val = value_func()
            output_vals.append(val)
    return dataclass(*output_vals)


rent_stock_inputs = populate_columns(
    [
        lambda: dollar_input("Current Monthly Rent", 2000),
        lambda: rate_input("Yearly Rent Increase", 3.0),
        lambda: rate_input("Stock Return Rate", 7.0),
        lambda: rate_input("Stock Tax Rate", 15.0)
    ],
    RentStockInputs
)

st.write(rent_stock_inputs)
