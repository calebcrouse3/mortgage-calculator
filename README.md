# TODO

- Tooltips with hover over and no (?)
- ICB ads
- Extra payments input/graph
- Insurance default value / estimation
- Calculate button
- Save selected chart lines to session state
- About page
- Chart hover over so red or green for profit or loss
- Specifics of capital gains and how it effects stock and home sale price
    - The 2 year window for capital gains tax free sale
- Opportunity cost and savings of extra payments or using profit to pay down principle
- Actual formula for renting vs ownership - reccomendations for rent vs own. 5 percent rule?
    - Based on the home, give the rental that will have the correct crossover point
- You need to make this much rental income to do 'X'
- Total returns versus downpayment analysis


# Deployment
Steps
- `make build`
- test container with `make run-docker`
- `make tar`
- Open peotry shell with `poetry shell`
- `cd ./cdk`
- `cdk synth` to check synthesis into cloud formation
- `cdk diff` to make sure there are changes to be pushed
- `cdk deploy`

Had to forward from app.mortgage-calculator to load balancer domain in aws console.

# Mortgage Notes
- What expense increases does inflation drive?
- Median growth in ppsf might be better for historical analysis than median home sale price because it corrects for size of homes

# Backlog Ideas
- Event Injector
- Make educational tutorial videos?
    - Impact of interest rates
    - Additional payments
    - Does PMI matter
    - Renting versus Buying
    - How to house hack
    - How to evaluate a rental
    - etc.
- Download printable report
- Save simulation inputs
- Upload previous simulation inputs
- Zillow link
- Refinancing calculator
- Market analysis using open source data indicators