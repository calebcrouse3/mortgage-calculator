import streamlit as st

class StateItem:
    _instance_counter = 0

    def __init__(self, default, rate=False):
        self.default = default
        self.rate = rate
        self.key = str(StateItem._instance_counter)
        StateItem._instance_counter += 1

        if self.key not in st.session_state:
            st.session_state[self.key] = default

    @property
    def val(self):
        if self.rate:
            return st.session_state[self.key] / 100
        return st.session_state[self.key]


class SessionStateInterface:
    def __init__(self):
        self.hide_text = StateItem(False)
        self.init_home_value = StateItem(300000)
        self.down_payment = StateItem(50000)
        self.interest_rate = StateItem(7.0, rate=True)
        self.yearly_home_value_growth = StateItem(3.0, rate=True)
        self.property_tax_rate = StateItem(1.0, rate=True)
        self.closing_costs_rate = StateItem(3.0, rate=True)
        self.pmi_rate = StateItem(0.5, rate=True)
        self.insurance_rate = StateItem(0.35, rate=True)
        self.init_hoa_fees = StateItem(100)
        self.init_monthly_maintenance = StateItem(100)
        self.inflation_rate = StateItem(3.0, rate=True)
        self.extra_monthly_payments = StateItem(200)
        self.number_of_payments = StateItem(12)
        self.rent = StateItem(1500)
        self.stock_growth_rate = StateItem(7.0, rate=True)
        self.rent_income = StateItem(0)
        self.rent_increase = StateItem(3.0, rate=True)
        self.stock_tax_rate = StateItem(15.0, rate=True)

    def clear(self):
        st.session_state.clear()
