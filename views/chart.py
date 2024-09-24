import streamlit as st
from .utils import Logger
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from .datastore import load_config, get_dev_stacks

### render charts
def plot_pie_chart(stack_counts, logger):
    method_name = __name__+".plot_pie_chart"
    fig, ax = plt.subplots()
    ax.pie(stack_counts.values(), labels=stack_counts.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.subheader("Tech Stacks as Pie Chart")
    st.pyplot(fig)
    logger.log(f"action:load, element:pie_chart", flag=4, name=method_name)
    
def plot_donut_chart(stack_counts, logger):
    method_name = __name__ + ".plot_donut_chart"
    fig, ax = plt.subplots()
    ax.pie(stack_counts.values(), labels=stack_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))
    ax.axis('equal')
    st.pyplot(fig)
    logger.log(f"action:load, element:donut_chart", flag=4, name=method_name)

def plot_histogram(stack_counts, logger):
    method_name = __name__ + ".plot_histogram"
    fig, ax = plt.subplots()
    ax.hist(list(stack_counts.values()), bins=10)
    plt.xlabel("Stack Count")
    plt.ylabel("Frequency")
    st.pyplot(fig)
    logger.log(f"action:load, element:histogram", flag=4, name=method_name)
    
def plot_bar_chart(stack_counts, logger):
    method_name = __name__ + ".plot_bar_chart"
    fig, ax = plt.subplots()
    ax.bar(stack_counts.keys(), stack_counts.values())
    plt.xticks(rotation=45, ha='right')
    st.subheader("Tech Stacks as Bar Chart")
    st.pyplot(fig)
    logger.log(f"action:load, element:bar_chart", flag=4, name=method_name)
    
def plot_horizontal_bar_chart(stack_counts,logger):
    method_name = __name__ + ".plot_horizontal_bar_chart"
    fig, ax = plt.subplots()
    ax.barh(list(stack_counts.keys()), list(stack_counts.values()))
    plt.xticks(rotation=45, ha='right')
    st.subheader("Tech Stacks as Horizontal Bar Chart")
    st.pyplot(fig)
    logger.log(f"action:load, element:horizontal_bar_chart", flag=4, name=method_name)

def display_chart_page(logger:Logger):
    st.header("Chart")
    config = load_config()
    ### select type of chart to show
    chart_type = st.selectbox("Select chart type", ("Pie Chart", "Donut Chart", "Bar Chart", "Horizontal Bar Chart", "Histogram"))
    
    ### convert stacks to df to visualize counts
    dev_stacks = get_dev_stacks(_logger=logger, endpoint=f"{config.get('API_URL')}/dev_stacks", database=config.get('DATABASE')) # list
    stack_counts = Counter(dev_stacks)
    top_10_stacks = stack_counts.most_common(10)
    
    ### col1 = selected chart, col2 = df of tech stacks with ['stack name', 'count of stacks'] as columns
    col1, col2 = st.columns([2, 1])
    with col1:
        seperator = 15
        if chart_type == "Pie Chart":
            plot_pie_chart(top_10_stacks, logger)
        elif chart_type == "Donut Chart":
            plot_donut_chart(top_10_stacks, logger)
        elif chart_type == "Bar Chart":
            plot_bar_chart(top_10_stacks, logger)
        elif chart_type == "Horizontal Bar Chart":
            plot_horizontal_bar_chart(top_10_stacks, logger)
        elif chart_type == "Histogram":
            plot_histogram(top_10_stacks, logger)
    with col2:
        seperator = 16
        st.subheader("Tech Stack List Top 10")
        stack_df = pd.DataFrame(top_10_stacks.items(), columns=['Stack', 'Count'])
        st.dataframe(stack_df)