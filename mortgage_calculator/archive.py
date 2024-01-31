import streamlit as st

def display_metrics_in_grid(metrics, num_columns):
    """
    Displays metrics in a grid layout with a specified number of columns.

    :param metrics: A dictionary of metrics where keys are labels and values are the metric values.
    :param num_columns: The number of columns in each row of the grid.
    """
    # Convert the metrics dictionary to a list of (key, value) pairs for easier chunking
    metrics_items = list(metrics.items())
    
    # Calculate the total number of rows needed
    total_rows = (len(metrics_items) + num_columns - 1) // num_columns
    
    for row in range(total_rows):
        # For each row, get the chunk of metrics to display
        start_index = row * num_columns
        end_index = start_index + num_columns
        metrics_chunk = metrics_items[start_index:end_index]

        # Create a row of columns and display each metric in a column
        for i, col in enumerate(st.columns(num_columns)):
            with col:
                if i < len(metrics_chunk):
                    key, value = metrics_chunk[i]
                    st.metric(label=key, value=value, delta="")