A better mortgage calculator

### TODO
- Tooltips
- Extra Payments Graph
- Switch to light theme
- ICB Ads
- Fix get_metrics function
- Revisit Insurance Estimation
- Not subtracting rental income correctly I dont think.
- Make chart yaxis horizontal
- EDA for rental comps home price comparison
- QA monthly and yearly df for all values
- Double check that X-axis for graphs correspond to correct data
- Verify Rental Comparison Setup is correct
- Run simulation button
- Keep selected lines in plotly as session state
- Auto increment session state key values
- Better summary
- Charts Charts Chart
- Metrics Metrics Metrics
- Call out highlights when they are display. The metrics. Say something like "highlights"
- Make format of highlights the same as summary for consistency
- Make a tips sections for navigating the calculator
- Give leads on each tab of questions this can help answer
- Use annotations on the charts instead of at the top
- Hide boarder box on expander and move arrow next to text

### Tech Notes
Had to forward from app.mortgage-calculator to load balancer domain in aws console.

### Mortgage Notes
Does inflation drive insurance increase, rental increase, HOA increase, etc?
Median growth in ppsf might be better than median home sale price because it corrects for size of homes

### Backlog Ideas
- home/stock selling Costs
- Event Injector
- Make a page that asks various questions and shows how the calculator can answer them
    - impact of interest rates
    - Should I make additional payments
    - What factors matters most
    - Does PMI matter
    - Renting versus Buying
    - How to house hack
    - How to assess a property
    - etc.
- Download report
- Save simulation
- Zillow link

### Data points to supply from regional lookup
- Median home price
- Median ppsf
- Median rent price across different property types
- Median rent ppsf