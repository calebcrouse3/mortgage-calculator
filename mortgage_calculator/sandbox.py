from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

from utils import *
from utils_finance import *
from session_state_interface import SessionStateInterface

def merge_simulations(sim_df_a, sim_df_b, append_cols, prefix):
        """
        Sim df A keeps all it columns
        Sim df B keeps the merge columns with a prefix and is joined to sim df A on index
        """
        sim_df_b = sim_df_b[append_cols]
        sim_df_b = sim_df_b.rename(columns={col: f"{prefix}_{col}" for col in append_cols})
        return sim_df_a.join(sim_df_b)
