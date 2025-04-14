# Backlog Ideas

- ICB ads
- Insurance default value / estimation
- Review and expand tax and sale assumptions for taxes and homes on different time lines
- Specifics of capital gains and how it effects stock and home sale price
    - The 2 year window for capital gains tax free sale
- Actual formula for renting vs ownership - reccomendations for rent vs own. 5 percent rule?
    - Based on the home, give the rental that will have the correct crossover point
- Total returns versus downpayment analysis
- Zillow link
- Refinancing calculator

# How the Mortgage Simulation Works

The mortgage calculator uses a comprehensive month-by-month simulation approach to model the financial aspects of homeownership over time. This simulation tracks various expenses, asset values, and alternative investment scenarios to provide a detailed comparison of different financial strategies.

## Core Simulation Logic

The simulation operates on a monthly basis for up to 30 years (360 months), tracking the following key components:

### Monthly Calculations
- **Principal and Interest**: Calculated using standard amortization formulas where monthly payment remains constant while the proportion of principal to interest changes over time
- **Loan Balance**: Updated monthly by subtracting principal payments (and any extra payments)
- **Home Value**: Appreciates according to the specified annual rate
- **PMI (Private Mortgage Insurance)**: Automatically calculated and canceled when either:
  - Equity reaches 20% of the current home value
  - Loan balance falls below 80% of the initial home value

### Expenses Tracked
- Mortgage principal and interest
- Property taxes (calculated as a percentage of home value)
- Homeowner's insurance
- HOA fees
- Maintenance costs
- Utilities
- PMI (when applicable)

### Annual Updates
At the end of each year, the simulation updates several values to reflect changing economic conditions:
- Property taxes (based on new home value)
- Insurance premiums
- HOA fees (adjusted for inflation)
- Utility costs (adjusted for inflation)
- Maintenance costs (as a percentage of current home value)
- Rent comparison values (for rent vs. own analysis)

## Alternative Investment Scenarios

The simulation runs parallel calculations to compare different financial strategies:

### Extra Payments Analysis
When extra mortgage payments are specified, the simulation:
1. Applies extra payments directly to the loan principal
2. Simultaneously tracks how those same funds would perform in an investment portfolio
3. Compares interest saved from extra payments versus potential investment returns

### Rent vs. Own Comparison
The simulation models an alternative scenario where instead of buying:
1. The initial cash outlay (down payment, closing costs, etc.) is invested in a portfolio
2. Monthly savings from renting vs. owning are added to the investment portfolio
3. Compares the financial outcomes of both scenarios over time

#### Net Worth Calculation

**Net Worth from Owning** is calculated as:
- Net Worth = Equity - Realtor Fees - Capital Gains Tax - Cumulative Cost of Ownership
- Equity = Home Value - Loan Balance
- Cumulative Cost of Ownership = Cumulative sum of all expenses other than principal
- Capital Gains Tax = Home Value - Adjusted Cost Basis
- Adjusted Cost Basis = Home Price + Rehab

**Net Worth from Renting** is calculated as:
- Net Worth = Portfolio Value - Capital Gains Tax - Total Rent Paid
- Capital Gains Tax = (Portfolio Value - Cost Basis) * Capital Gains Tax Rate
- Cost Basis = Portfolio Value - Cash Outlay - Additional Investment
- Additional Investment = Cumulative Total Expenses - Cumulative Rent Comparison Expenses

## Sale Proceeds Calculation

When analyzing potential home sale scenarios, the simulation accounts for:
- Realtor fees
- Adjusted cost basis (purchase price plus improvements)
- Capital gains calculations
- Net proceeds after all selling expenses

## Mathematical Formulas

### Monthly Mortgage Payment
The standard amortization formula is used to calculate the fixed monthly payment:

```
Monthly Payment = Loan Amount × (Monthly Rate × (1 + Monthly Rate)^n) / ((1 + Monthly Rate)^n - 1)
```
Where:
- Monthly Rate = Annual Interest Rate / 12
- n = Total Number of Payments (Years × 12)

### Asset Growth
Assets like home value and investment portfolios grow according to:

```
Future Value = Present Value × (1 + Annual Growth Rate)^(Months/12)
```

This comprehensive simulation approach allows for detailed financial planning and comparison of different mortgage and investment strategies over time.
