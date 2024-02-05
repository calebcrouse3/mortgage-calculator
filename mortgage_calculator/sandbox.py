from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

from utils import *
from utils_finance import *
from st_text import *
from utils_inputs import *

from session_state_interface import SessionStateInterface


import streamlit as st

# initialize sessions state
# create input fields linked to session state

# Initialize session state for inputs if not already done
if 'input_1' not in st.session_state:
    st.session_state['input_1'] = 0  # Default value
if 'input_2' not in st.session_state:
    st.session_state['input_2'] = 0  # Default value

# Input fields
input_1 = st.number_input('Input 1', key='input_1')
input_2 = st.number_input('Input 2', key='input_2')


# Function to run when calculate button is pressed
def calculate():
    # Here, you would use the values stored in the session state for computation
    result = st.session_state['input_1'] + st.session_state['input_2']
    st.write(f"Result: {result}")

def main():
    # Calculate button
    if st.button('Calculate'):
        calculate()

main()
