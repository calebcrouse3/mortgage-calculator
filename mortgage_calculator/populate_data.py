import streamlit as st
from streamlit import session_state as ssts
from enum import Enum

class AutoValueEnum(Enum):
    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if isinstance(value, Enum):
            return value.value
        return value


class Key(AutoValueEnum):
    init_home_value = "init_home_value"


def initialize_session_state():
    ssts[Key.init_home_value] = 1000

initialize_session_state()

st.write(ssts[Key.init_home_value])
