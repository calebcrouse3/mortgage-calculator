def get_monthly_payment_amount(loan_amount, interest_rate, years=30):
    monthly_rate = interest_rate / 12 / 100
    n_payments = years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) \
        / ((1 + monthly_rate)**n_payments - 1)
    return monthly_payment


def get_monthly_interest_payment(loan_balance, interest_rate):
    monthly_rate = interest_rate / 12 / 100
    return loan_balance * monthly_rate


def get_monthly_principal_payment(monthly_payment, interest_payment):
    return monthly_payment - interest_payment


def get_monthly_property_tax(home_value, property_tax_rate):
    return (home_value * property_tax_rate / 100) / 12


def get_monthly_insurance_cost(home_value, insurance_rate):
    return (home_value * insurance_rate / 100) / 12


def get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value):
    """
    Calculate Monthly PMI
    
    PMI gets cancelled when equity >= 20% of the home value, 
    or loan balance <= 80% of the init home value
    """
    equity = home_value - loan_balance
    if equity < 0.2 * home_value or loan_balance > 0.8 * init_home_value:
        return (loan_balance * pmi_rate / 100) / 12
    else:
        return 0


# a few different functions to calculate the total asset value or increment it

def get_asset_value(initial_value, growth_rate, years):
    return initial_value * (1 + growth_rate / 100)**years


def get_asset_value(initial_value, growth_rate, months, monthly_contribution=0):
    monthly_growth = growth_rate / 12
    total_value = initial_value

    for _ in range(1, months + 1):
        total_value = total_value * (1 + monthly_growth) + monthly_contribution

    return total_value


def get_asset_monthly_growth(value, yearly_growth_rate, contribution=0):
    monthly_growth = yearly_growth_rate / 12
    return value * (1 + monthly_growth) + contribution