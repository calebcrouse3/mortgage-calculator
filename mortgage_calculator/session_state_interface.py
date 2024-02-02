import streamlit as st

class StateItem:

    def __init__(self, default, key, rate=False):
        self.default = default
        self.rate = rate
        self.key = key

        if self.key not in st.session_state:
            st.session_state[self.key] = default

    @property
    def val(self):
        if self.rate:
            return st.session_state[self.key] / 100
        return st.session_state[self.key]


class SessionStateInterface:

    def __init__(self):
        self.counter = self.counter_generator()

        def create_item(val, rate=False):
            # Use next(self.counter) to get the next value from the generator
            key = f"state_item_{next(self.counter)}"
            return StateItem(val, key, rate)

        # Define counter_generator as a static method so it can be called without an instance
        self.hide_text = create_item(False)
        self.init_home_value = create_item(300000)
        self.down_payment = create_item(50000)
        self.interest_rate = create_item(7.0, rate=True)
        self.yearly_home_value_growth = create_item(3.0, rate=True)
        self.property_tax_rate = create_item(1.0, rate=True)
        self.closing_costs_rate = create_item(3.0, rate=True)
        self.pmi_rate = create_item(0.5, rate=True)
        self.insurance_rate = create_item(0.35, rate=True)
        self.init_hoa_fees = create_item(100)
        self.init_monthly_maintenance = create_item(100)
        self.inflation_rate = create_item(3.0, rate=True)
        self.extra_monthly_payments = create_item(200)
        self.number_of_payments = create_item(12)
        self.rent = create_item(1500)
        self.stock_growth_rate = create_item(7.0, rate=True)
        self.rent_income = create_item(0)
        self.rent_increase = create_item(3.0, rate=True)
        self.stock_tax_rate = create_item(15.0, rate=True)

    @staticmethod
    def counter_generator():
        counter = 0
        while True:
            yield counter
            counter += 1

    def clear(self):
        st.session_state.clear()
