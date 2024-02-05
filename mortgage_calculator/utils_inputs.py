import streamlit as st


def rate_input(label, key=None, min_value=0.0, max_value=99.0, step=0.1, asterisk=False, help=None):
    if asterisk:
        label = ":orange[**]" + label
    
    percent = st.number_input(
        label=f"{label} (%)",
        min_value=min_value,
        max_value=max_value,
        step=step,
        key=key,
        help=help,
        on_change=None
    )
    return percent


def dollar_input(label, key=None, min_value=0, max_value=1e8, step=10, asterisk=False, help=None):
    """Function that will calculate the step input based on the default value.
    The step is 1eN where N is one less than the number of digits in the default value.
    """

    if asterisk:
        label = ":orange[**]" + label

    return st.number_input(
        f"{label} ($)",
        min_value=int(min_value), 
        max_value=int(max_value),
        step=int(step),
        key=key,
        help=help,
        on_change=None
    )


def populate_columns(values, cols=3):
    output_vals = []
    columns = st.columns(cols)
    assert len(columns) >= len(values)
    for col, value_func in zip(columns[:len(values)], values):
        with col:
            val = value_func()
            output_vals.append(val)
    return output_vals