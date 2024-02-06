"""Financial calculations helper functions"""

def get_amortization_payment(loan_amount, interest_rate, years=30):
    monthly_rate = interest_rate / 12
    n_payments = years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) \
        / ((1 + monthly_rate)**n_payments - 1)
    return monthly_payment


def get_total_interest_paid(loan_amount, interest_rate, years=30):
    """Calculate the total interest paid over the life of the loan."""
    total_paid = get_amortization_payment(loan_amount, interest_rate, years) * years * 12
    return total_paid - loan_amount


def add_growth(value, yearly_growth_rate, months, monthly_contribution=0):
    """Calculate the value of an asset after a number of months"""

    def monthly_growth(value, yearly_growth_rate, months):
        return value * (1 + yearly_growth_rate)**(months / 12)


    if monthly_contribution == 0:
        return monthly_growth(value, yearly_growth_rate, months)
    
    else:
        total_value = value

        for _ in range(months):
            total_value = monthly_growth(value, yearly_growth_rate, 1) + monthly_contribution

        return total_value


# TODO clean up PMI shit

def cancel_pmi_from_equity(home_value, loan_balance):
    """Returns true when equity >= 20% of the home value"""
    equity = home_value - loan_balance
    return equity >= 0.2 * home_value


def cancel_pmi_from_loan_balance(init_home_value, loan_balance):
    """Returns true when loan balance <= 80% of the init home value"""
    return loan_balance <= (0.8 * init_home_value)


def get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value):
    """
    Calculate Monthly PMI. PMI gets cancelled when equity >= 20% of the home value, 
    or loan balance <= 80% of the init home value
    """

    if cancel_pmi_from_equity(home_value, loan_balance) or \
        cancel_pmi_from_loan_balance(init_home_value, loan_balance):
        return 0
    else:
        return (loan_balance * pmi_rate) / 12