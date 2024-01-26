from enum import Enum

class AutoValueEnum(Enum):
    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if isinstance(value, Enum):
            return value.value
        return value

class Key(AutoValueEnum):

    # Mortgage
    region = "00"
    init_home_value = "01"
    down_payment = "02"
    interest_rate = "03"
    yearly_home_value_growth = "04"
    property_tax_rate = "05"

    # Other Costs
    closing_costs_rate = "06"
    pmi_rate = "07"
    insurance_rate = "08"
    init_hoa_fees = "09"
    init_monthly_maintenance = "10"
    inflation_rate = "11"

    # extra mortgage payments
    extra_monthly_payments = "12"
    number_of_payments = "13"

    # Selling
    realtor_rate = "14"
    sell_closing_costs_rate = "15"
    additional_selling_costs = "16"
    
    # Investing
    rent = "17"
    rent_increase = "18"
    stock_growth_rate = "19"
    stock_tax_rate = "20"

