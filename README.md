A better mortgage calculator


### Tech Notes
Had to forward from app.mortgage-calculator to load balancer domain in concsole.

### Mortgage Notes
Inflation?
Escrow / earnest money?
PMI can get cancelled when:
- remaining loan balance < 80 percent of homes original value
- equity > 20 percent of current home value
Each year, your PMI is recalculated using your current loan balance.

Amortization is paying off debt over time in equal installments
What are the costs of refinancing?
Whats an even benchmark to compare rent price and home price. Price per square foot?
Does inflation determine rental increase, insurance, other things? Can it all be boiled down to one number?
Difference between monthly and biweekly payments? What does that do

Have the first page be tutorial narrative style top to bottom but you can click to a page with just the numbers

I think median growth in ppsf might be better than median home sale price because it corrects for size of homes

### Biz notes
Look into Icanbuy for ad revenue
Call this a no compromises mortgage calculator. We leave nothing out.

### TODO
- Summary with numbers at the top
- unit test for summary numbers with a fixed input
- Add PMI to interest to keep it simple
- keep selected lines in ploty as session state
- Show multiple values on graph at one time for hover over
- Add costs of selling a home to home equity
- Home maintenance upgrades and repairs
- Pie chart for inital monthly breakdown?
- stack charts toggle
- Feature for extra principle payments on top of base mortgage rate
- Calculate button that runs the whole thing versus updating on each widget update
- Database lookups for home price, home growth, tax rates, rent price, rent growth?
- taxes and insurance update yearly? Yes.
- yearly numbers versus monthly?
- event injector for refinance, increased home growth, etc




# TODO how does compounding work for home value growth, rental price increase, stock market value growth.
# Need to investigate how to model this correctly. Compounding year/ month/ day?
# could calculate the growth based on the year increase, time passed, and inital price.

# need to update some things on yearly basis like rent, tax, and insurance
# assumption - you start with your downpayment and make no other money. Have no salary

# add part for additional payments to principle early on. Which would also be added to stock market
# what taxes and fees need to be added to the selling of a home to mirror the taxes applied to stock market profits

# can rent out you house, poket the rent based on current price, and buy another house???
