import streamlit as st
from .utils import Logger
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from .datastore import load_config, get_dev_stacks

### render charts
def plot_pie_chart(stack_counts):
    labels, counts = zip(*stack_counts)
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.subheader("Tech Stacks as Pie Chart")
    st.pyplot(fig)
    
def plot_donut_chart(stack_counts):
    labels, counts = zip(*stack_counts)
    fig, ax = plt.subplots()
    ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.4))
    ax.axis('equal')
    st.pyplot(fig)

def plot_histogram(stack_counts):
    counts = [count for _, count in stack_counts]
    fig, ax = plt.subplots()
    ax.hist(counts, bins=10)
    plt.xlabel("Stack Count")
    plt.ylabel("Frequency")
    st.pyplot(fig)
    
def plot_bar_chart(stack_counts):
    labels, counts = zip(*stack_counts)
    fig, ax = plt.subplots()
    ax.bar(labels, counts)
    plt.xticks(rotation=45, ha='right')
    st.subheader("Tech Stacks as Bar Chart")
    st.pyplot(fig)
    
def plot_horizontal_bar_chart(stack_counts):
    labels, counts = zip(*stack_counts)
    fig, ax = plt.subplots()
    ax.barh(labels, counts)
    plt.xticks(rotation=45, ha='right')
    st.subheader("Tech Stacks as Horizontal Bar Chart")
    st.pyplot(fig)

def display_chart_page(logger:Logger):
    st.header("Chart")
    method_name = __name__ + ".display_chart_page"
    config = load_config()
    try:
        ### select type of chart to show
        chart_type = st.selectbox("Select chart type", ("Pie Chart", "Donut Chart", "Bar Chart", "Horizontal Bar Chart", "Histogram"))
        
        ### convert stacks to df to visualize counts
        dev_stacks = get_dev_stacks(_logger=logger, endpoint=f"{config.get('API_URL')}/dev_stacks", database=config.get('DATABASE')) # list
        stack_counts = Counter(dev_stacks)
        top_10_stacks = stack_counts.most_common(10)
        
        ### col1 = selected chart, col2 = df of tech stacks with ['stack name', 'count of stacks'] as columns
        col1, col2 = st.columns([2, 1])
        with col1:
            if chart_type == "Pie Chart":
                plot_pie_chart(top_10_stacks)
            elif chart_type == "Donut Chart":
                plot_donut_chart(top_10_stacks)
            elif chart_type == "Bar Chart":
                plot_bar_chart(top_10_stacks)
            elif chart_type == "Horizontal Bar Chart":
                plot_horizontal_bar_chart(top_10_stacks)
            elif chart_type == "Histogram":
                plot_histogram(top_10_stacks)
        with col2:
            st.subheader("Tech Stack List Top 10")
            stack_df = pd.DataFrame(top_10_stacks, columns=['Stack', 'Count'])
            st.dataframe(stack_df)
    except Exception as e:
        logger.log(f"Exception occurred while displaying charts:{e}", flag=1, name=method_name)