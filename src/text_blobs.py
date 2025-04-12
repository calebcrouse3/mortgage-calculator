annualized_coc_roi = """This gives the cash on cash return in a particular year ignoring any proprty sale 
income. Its the cash flow in a particular year divided by the total out of pocket cash
initially invested."""

total_return = """this gives the total return after a number of years if the home is sold at the end of the year.
It captures the profit from income (or loss if income doesnt cover all expenses), 
and the after tax/fee profit from selling the home at the end of a particular year. 
This is calculated as the after tax/fee sale income from the home (which depends on how much equity 
you have in the home) minus the out of pocket cash initially invested including the downpayment. Some might refer to the
total return as the total profit, but generally the term profit should only be
used when referring to the rental income that a property generates. The total return 
includes this profit and the money from the sale of the home."""


net_worth_post_sale = """This assumes your net worth before making any home purchase is 0 and so your net worth at the end of any year
is any profit (or loss) from owning the property as well as the amount of equity in the home at the end of the year.
This encompasses the total net value of assets (cash and property) you have.
Its basically the same at total return ecxept it uses the equity in the home instead of profit from selling the home.
Meaning the down payment is still part of you networth, unlike your total return,
and you didnt have to pay fees to sell the home."""

roi = """This is the total RATE of return for the time period up to a particular year if the home is sold.
It is just the total return after a number of years divide by the out of pocket costs initially invested."""

annualized_roi = """This is the annualized yearly return on investment for the time period up to a particular year 
if the home is sold at the end of that year. This is the same as the ROI, but annualized."""

internal_irr = """This is the internal rate of return for the time period up to a 
particular year if the home is sold at the end of that year.
The IRR is the annualized yearly return on investment for the time period up to a particular year 
discounted by the time value of money. One way to interpret the IRR is that you would make as much money
on this investment as you would if you had invested the out of pocket cash in a different investment
with this growth rate. This isnt quite right because its the hurdle discount rate which 
factors in risk as well as returns. Explore more.
"""

noi="""This is the monthly net operating income and net income after financing (cash flow) for each year."""



########################################################################
#      Expenses                                          
########################################################################

"""This category contains information about the costs of owning a home and 
mortgage and the value of your home overtime. It can be used as a simple 
mortgage calculator. If you've filled out the rental income section, you can 
also see some simple comparisons between youre costs and income. The 'Extra 
Payment Analysis' tab will show you the impact of making extra payments on your 
mortgage and whether it is a good idea given other investment options."""


########################################################################
#      Extra Payments                                                  #
########################################################################
    
"""Many home owners consider making extra payments towards there mortgage to save on interest.
This tab allows you to add extra monthly payments and see the effect of interest savings over time.
Its important to also consider if that extra money would have been better spent somewhere else.
This chart also tells you how much you could have made if you had instead invested that money in a 
stock portfolio with continuous growth. The main variables that effect the difference between these 
two options are the difference between interest rate on the loan and the growth rate of the stock portfolio.
In this scenario. Its also important to consider that the stock market is highly variable and returns, especially
in the short term, may not be continuous. Where as the interest savings from extra payments are guaranteed.
Conversely, the savings on interest from extra payments take time to accumulate, 
where as the stock portfolio has the potential to grow immediately. Extra mortgage payments 
with have a greater effect on the interest savings the earlier they are made."""


########################################################################
#      Rent vs Own                                                     #
########################################################################

"""
This tab compares the total returns of owning a home versus renting.
In this scenario, instead of buying a home, you would have put all the out of pocket cash into the stock market
and live in a rental. In any month, if the expenses of owning
a home are greater than rent, that extra cash is invested into the stock market.
This captures the opportunity cost of capital. In many situations, if you arent house hacking,
you should expect a loss in the short to medium term for either decision, but by comparing the two,
you can figure out which one saves you more money in the long run, and how long you 
have to live in a home to make it worth it over renting.
"""


########################################################################
#      Investment                                                      #
########################################################################

"""This catgory shows common figures and metrics used to asses the quality of a
rental investment. This will be most useful if you plan on making some rental income 
with this property, but many of the figures are still useful in just assessing
home ownership as an invesment. If you havent spent time analysing rental properties,
the terms and figures here might be confusing or unfamiliar. Navigate to the 'About' tab
to learn more about these concepts and how to use them."""


########################################################################
#      Home                                                            #
########################################################################


"Uncompromising Mortgage Calculator"

"Introduction"
"""Not your fathers mortgage calculator. This tools runs a month over month 
simulation accounting for all factors and the 
interplay between them. Expenses, rental income, reinvestment, 
growth rates, taxes and fees, opportunity costs, and house hacking are all 
considered."""


"Example Use Cases"
"""
- What are the short and long term costs of owning a home?
- Is this rental property a good deal?
- Should I rent or buy for my primary residence?
- Should I pay down my loan with rental profits?
- How much of my mortgage can I offset by house hacking?
"""

"Getting Started"
"""
- Fill out the fields in sidebar. They are ogranized into logical groups. Many inputs are prepopulated with reasonable defaults.
- Start by adding a home price and down payment. If youre going to rent out any part of this property, fill out the fields in the rental income exapnder.
- Click across the tabs to see different charts and metrics. 
- Some tabs are straightforward and some might require familiazing yourself with certain concepts which you can explore in the 'About' tab. 
- Look at tooltips for more information if youre unsure what to do with an input. 
- For more in depth details, navigate to the 'About' tab.
"""

"Tech Tips"
"""
- Hover over charts to see exact values
- Click and drag to zoom in on a particular area 
- Adjust chart settings in the sidebar under the chart options expander
- Collapse the sidebar by clicking the x in the top right corner of the sidebar 
- Expanders have a ^ in the top corner of the box and can be collapsed by clicking the top of the box
"""