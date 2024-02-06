import unittest

from mortgage_calculator.utils_finance import *

class TestFinancialFunctions(unittest.TestCase):

    def test_get_monthly_payment_amount(self):
        loan_amount = 100000
        interest_rate = 0.07

        years = 30
        monthly_payment = get_amortization_payment(loan_amount, interest_rate, years)
        expected_payment = 665.302
        self.assertAlmostEqual(monthly_payment, expected_payment, places=2)

        years = 15
        monthly_payment = get_amortization_payment(loan_amount, interest_rate, years)
        expected_payment = 898.828
        self.assertAlmostEqual(monthly_payment, expected_payment, places=2)


    def test_get_monthly_pmi(self):
        """PMI gets cancelled when:
        equity >= 20% of the home value, 
        or loan balance <= 80% of the init home value
        """

        # cancel pmi from loan balance
        init_home_value = 300
        home_value = 100
        loan_balance = 200
        pmi_rate = 0.01
        monthly_pmi = get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value)
        self.assertTrue(cancel_pmi_from_loan_balance(init_home_value, loan_balance))
        self.assertFalse(cancel_pmi_from_equity(home_value, loan_balance))
        self.assertEqual(monthly_pmi, 0)

        # cancel pmi from equity
        init_home_value = 300
        home_value = 400
        loan_balance = 280
        pmi_rate = 0.01
        monthly_pmi = get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value)
        self.assertFalse(cancel_pmi_from_loan_balance(init_home_value, loan_balance))
        self.assertTrue(cancel_pmi_from_equity(home_value, loan_balance))
        self.assertEqual(monthly_pmi, 0)

        # pay pmi
        init_home_value = 300
        home_value = 301
        loan_balance = 280
        pmi_rate = 0.01
        monthly_pmi = get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value)
        self.assertFalse(cancel_pmi_from_loan_balance(init_home_value, loan_balance))
        self.assertFalse(cancel_pmi_from_equity(home_value, loan_balance))
        self.assertAlmostEqual(monthly_pmi, loan_balance * pmi_rate / 12, places=2)


    def test_add_growth(self):
        initial_value = 100
        growth_rate = 0.05
        months = 12
        monthly_contribution = 0
        asset_value = add_growth(initial_value, growth_rate, months, monthly_contribution)
        self.assertAlmostEqual(asset_value, 105, places=2)

        initial_value = 100
        growth_rate = 0.05
        months = 12 * 2
        monthly_contribution = 0
        asset_value = add_growth(initial_value, growth_rate, months, monthly_contribution)
        self.assertAlmostEqual(asset_value, 110.25, places=2)

        initial_value = 100
        growth_rate = 0.05
        months = 1
        monthly_contribution = 0
        asset_value = add_growth(initial_value, growth_rate, months, monthly_contribution)
        self.assertAlmostEqual(asset_value, 100.407, places=2)

        initial_value = 100
        growth_rate = 0.05
        months = 1
        monthly_contribution = 1
        asset_value = add_growth(initial_value, growth_rate, months, monthly_contribution)
        self.assertAlmostEqual(asset_value, 101.407, places=2)


if __name__ == '__main__':
    unittest.main()
