import streamlit as st

# This dict needs to be provided both for the session item and the input field
# These probably need to be updated occasionally
ALT_INVESTMENTS = {
    "0.5% (Savings Account)": 0.5,
    "1.1% (10 Year CDs)": 1.1,
    "1.8% (SP500 Dividends)": 1.8,
    "2.5% (Money Market)": 2.5,
    "4.3% (10 Year US Treasury)": 4.3,
    "4.4% (30 Year US Treasury)": 4.4,
    "7.0% (SP500)": 7.0,
}


class StateItem:
    def __init__(self, default, key, rate=False, select_box_lookup=None):
        self.default = default
        self.rate = rate
        self.key = key
        self.select_box_lookup = select_box_lookup

        if self.key not in st.session_state:
            #if self.select_box_lookup:
            #    st.session_state[self.key] = list(self.select_box_lookup.keys())[0]
            st.session_state[self.key] = default

    @property
    def val(self):
        if self.select_box_lookup:
            if self.rate:
                return self.select_box_lookup[st.session_state[self.key]] / 100
            return self.select_box_lookup[st.session_state[self.key]]
        if self.rate:
            return st.session_state[self.key] / 100
        return st.session_state[self.key]


class SessionStateInterface:

    def __init__(self):
        self.counter = self.counter_generator()

        def create(val, rate=False, select_box_lookup=None):
            key = f"state_item_{next(self.counter)}"
            return StateItem(val, key, rate, select_box_lookup)

        self.home_price = create(300000)
        self.rehab = create(1000)
        self.down_payment = create(50000)
        self.closing_costs_rate = create(3.0, rate=True)
        self.interest_rate = create(6.5, rate=True)
        self.pmi_rate = create(0.5, rate=True)
        self.yr_property_tax_rate = create(1.0, rate=True)
        self.yr_home_appreciation = create(3.0, rate=True)
        self.yr_insurance_rate = create(0.35, rate=True)
        self.mo_hoa_fees = create(0)
        self.yr_maintenance = create(1.5, rate=True)
        self.yr_inflation_rate = create(3.0, rate=True)
        self.mo_rent_income = create(0)
        self.mo_other_income = create(0)
        self.yr_rent_increase = create(3.0, rate=True)
        self.mo_utility = create(200)
        self.management_rate = create(10.0, rate=True)
        self.vacancy_rate = create(5.0, rate=True)
        self.paydown_with_profit = create(False)
        self.rent_exp = create(1500)
        self.xlim = create(30)
        self.chart_mode = create("Lines")
        self.capital_gains_tax_rate = create(15.0, rate=True)
        self.income_tax_rate = create(25.0, rate=True)
        self.realtor_rate = create(6.0, rate=True)

        self.mo_extra_payment = create(300)
        self.num_extra_payments = create(12)

        self.extra_payments_portfolio_growth = create(list(ALT_INVESTMENTS.keys())[0], rate=True, select_box_lookup=ALT_INVESTMENTS)
        self.rent_surplus_portfolio_growth = create(list(ALT_INVESTMENTS.keys())[0], rate=True, select_box_lookup=ALT_INVESTMENTS)


    # Define counter_generator as a static method so it can be called without an instance
    @staticmethod
    def counter_generator():
        counter = 0
        while True:
            yield counter
            counter += 1

    def clear(self):
        st.session_state.clear()
