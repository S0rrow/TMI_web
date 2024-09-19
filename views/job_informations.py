import streamlit as st
import pandas as pd
import json, math, os
import matplotlib.pyplot as plt
from collections import Counter
from .utils import Logger
from .datastore import call_dataframe, get_search_history, save_search_history, load_config, get_unique_column_values, get_column_names, get_table_row_counts, call_stacked_columns, get_elements_from_stacked_element, get_dev_stacks

### dialog
@st.dialog("Detailed Information", width="large")
def detail(logger:Logger, config:dict, pid:int, crawl_url:str):
    method_name = __name__ + ".detail"
    logger.log(f"action:load, element:detail_page_{pid}",flag=4, name=method_name)
    parent_path = os.path.dirname(os.path.abspath(__file__))
    data_load_state = st.text("Loading data...")
    try:
        url = config.get('API_URL')
        database = config.get('DATABASE')
        table = config.get('TABLE')
        query = f"SELECT * FROM {table} WHERE pid = {pid} AND crawl_url = '{crawl_url}';"
        row_df = call_dataframe(logger, endpoint=f"{url}/query", database=database, query=query)
        data_load_state.text(f"Data loaded.")
        col1, col2 = st.columns([2,8])
        with col1:
            st.logo(f"{parent_path}/../images/horizontal.png", icon_image=f"{parent_path}/../images/logo.png")
        with col2:
            st.header(f"{row_df['job_title'].values[0]}")
            st.subheader(f"{row_df['company_name'].values[0]}")
        st.subheader(f"직무 유형")
        job_categories = get_elements_from_stacked_element(logger, row_df, 'job_categories')
        for job_category in job_categories:
            st.markdown(f"- {job_category}")
        
        st.subheader(f"산업 유형")
        industry_types = get_elements_from_stacked_element(logger, row_df, 'industry_types')
        for industry_type in industry_types:
            st.markdown(f"- {industry_type}")
        
        st.subheader(f"Dev Stacks")
        dev_stacks = get_elements_from_stacked_element(logger, row_df, 'dev_stacks')
        for stack in dev_stacks:
            st.markdown(f"- {stack}")
        
        st.subheader(f"직무 요구사항")
        job_requirements = get_elements_from_stacked_element(logger, row_df, 'job_requirements')
        for job_requirement in job_requirements:
            st.markdown(f"- {job_requirement}")
        
        st.subheader(f"우대사항")
        job_prefers = get_elements_from_stacked_element(logger, row_df, 'job_prefers')
        for job_prefer in job_prefers:
            st.markdown(f"- {job_prefer}")

    except Exception as e:
        st.write(f"Exception:{e}")
        logger.log(f"Exception occurred while getting detailed dataframe from api: {e}", flag=1, name=method_name)

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

### render filters if user wants to filter data and search specific records
def display_filters(logger:Logger, search_history:pd.DataFrame, config:dict) -> dict:
    '''
    Generate filters for each column in the dataframe, and return filter.
    - logger: logger for logging events
    - search_history: dataframe to store search history
    - column_to_visualize: dictionary which stores column names as keys and boolean values as values for determining which column to show
    - config: configurations loaded from config file
    '''
    method_name = __name__ + ".display_filters"
    seperator = -1
    # Get the latest search term for the current session
    if search_history is not None and not search_history.empty:
        seperator = 0
        if len(search_history) == 1:
            latest_search_term = json.loads(search_history.iloc[0]['search_term'])
        else:
            latest_search_term = json.loads(search_history.iloc[-1]['search_term'])
    else:
        latest_search_term = {}
    
    try:
        filter_keys = {
            'search_keyword':"검색 키워드",
            'company_name':"회사 이름",
            'job_title':"직무 이름",
            'required_career':"경력 여부",
            'start_date':"공고 시작일",
            'end_date':"공고 종료일",
            'dev_stack':"기술 스택",
        }
        st.write(filter_keys['search_keyword'])
        search_keyword = st.text_input()
        st.write(filter_keys['company_name'])
        
        company_name = st.multiselect(filter_keys['company_name'], )
        
        # selected_stacks = st.multiselect(f"{column}", unique_values, default=default_filter)
        
        return latest_search_term

    except Exception as e:
        logger.log(f"Exception occurred while displaying filters at seperator #{seperator}: {e}", flag=1, name=method_name)
        return latest_search_term

### final dataframe
def generate_dataframe(logger:Logger, config:dict, search_terms:dict, is_filtered:bool, limit:int, offset:int, data_load_state)->pd.DataFrame:
    '''
        load final dataframe given from conditions
        - logger: logger
        - config: configurations loaded from config.json
        - search_terms: if dataframe is to be filtered, use search terms to modify query statement
        - is_filtered: boolean to configure whether to show filtered dataframe or not
        - data_load_state: streamlit text widget to tell whether data is loaded or not
    '''
    method_name = __name__ + ".generate_dataframe"
    database = config.get('DATABASE')
    table = config.get('TABLE')
    query = f"SELECT * FROM {table} WHERE "
    if is_filtered:
        # Create conditions for each column
        conditions = []
        for column, values in search_terms.items():
            # Escape single quotes in values
            escaped_values = ["'" + value.replace("'", "''") + "'" for value in values]
            # Create a condition for each column
            conditions.append(column + " IN (" + ', '.join(escaped_values) + ")")
        # join all conditions with AND statement
        query += ' AND '.join(conditions)
        if len(conditions) == 0:
            query = f"SELECT * FROM {table} LIMIT {limit} OFFSET {offset}"
    else:
        query = f"SELECT * FROM {table} LIMIT {limit} OFFSET {offset}"
    url = config.get('API_URL')
    endpoint_query = f"{url}/query"
    try:
        df = call_dataframe(logger, endpoint_query, database, query)
        if df is None or df.empty:
            logger.log(f"dataframe is empty: {e}", flag=0, name=method_name)
            data_load_state.text("No data found.")
            return None
        data_load_state.text("Data loaded from st.cached_data")
        return df
    except Exception as e:
        data_load_state.text(f"Failed to load data: {e}")
        logger.log(f"Excpetion occurred while generating dataframe: {e}", flag=1, name=method_name)
        return None

### pagination
def display_paginated_dataframe(logger:Logger, config:dict, row_count:int, rows_per_page:int, is_filtered:bool, search_terms:dict, visible_columns:list, data_load_state):
    '''
        display final pagination on streamlit
        arguments:
        - logger: Logger for logging
        - config: configuration dictionary
        - row_count: total count of row
        - rows_per_page: rows to show per page
        - is_filtered: indicator for whether dataframe to generate is filtered or not
        - search_terms: filter for dataframe
        - visible_columns: columns to show
        - data_load_state: streamlit widget to indicate data load state
    '''
    method_name = __name__ + ".display_paginated_dataframe"
    
    try:
        num_pages = math.ceil(row_count / rows_per_page)
        if not st.session_state.get('current_page',False):
            st.session_state['current_page'] = 0
        
        page_list = [f"{i+1}" for i in range(num_pages)]
        
        job_infos_view_tabs = st.tabs(page_list)
        for index in range(num_pages):
            st.session_state.current_page = index
            with job_infos_view_tabs[st.session_state.current_page]:
                logger.log(f"action:load, element:job_infos_view_tabs_{st.session_state.current_page}", flag=4, name=method_name)
                # 시작점
                offset = st.session_state.current_page * rows_per_page
                # row를 몇개까지 출력할지
                limit = rows_per_page if (offset + rows_per_page) <= row_count else row_count - offset
                ### 버튼이 눌렸을 경우, 최종적으로 필터링된 데이터프레임 시각화
                seperator = 10
                result_df = generate_dataframe(logger, config, search_terms=search_terms, is_filtered=is_filtered, data_load_state=data_load_state, limit=limit, offset=offset)
                if result_df is None or result_df.empty:
                    result_df = pd.DataFrame()
                    st.write("No result found.")
                else:
                    for row_index, row in result_df.iterrows():
                        row_container = st.container(border=True)
                        with row_container:
                            col1, col2 = st.columns([10,1])
                            sliced_row_df = pd.DataFrame(row.loc[visible_columns])
                            row_df = pd.DataFrame(row).transpose()
                            with col1:
                                st.table(data=sliced_row_df.transpose().reset_index(drop=True))
                            with col2:
                                detail_btn = st.button(f"자세히 보기", key=row_index+offset)
                                if detail_btn:
                                    logger.log(f"action:click, element:detail_button_{row_index}",flag=4, name=method_name)
                                    pid = int(row_df['pid'].values[0])
                                    crawl_url = str(row_df['crawl_url'].values[0])
                                    detail(logger=logger, config=config, pid=pid, crawl_url=crawl_url)
    except Exception as e:
        logger.log(f"Exception occurred while paginating final dataframe: {e}", flag=1, name=method_name)
### page display
def display_job_informations(logger):
    '''
        display job informations retreived from given url
    '''
    ### seperator for debug
    seperator = -1
    method_name = __name__ + ".display_job_informations"
    try:
        config = load_config()
        url = config.get("API_URL")
        database = config.get("DATABASE")
        if 'job_info_filtered' not in st.session_state:
            st.session_state['job_info_filtered'] = False
        table = config.get('TABLE')
        seperator = 0
        st.title("Job Information - Tech Stack Visualizations")
        logger.log(f"action:load, element:title",flag=4, name=method_name)
        st.header("Job Informations")
        logger.log(f"action:load, element:header",flag=4, name=method_name)
        data_load_state = st.text('Loading data...')
        logger.log(f"action:load, element:data_load_state",flag=4, name=method_name)
        seperator = 1
        
        ### endpoint로부터 column들의 목록과 메타데이터를 먼저 받아온다.
        endpoint_columns = f"{url}/columns"
        total_columns = get_column_names(logger, endpoint_columns, database, table)
        endpoint_row_count = f"{url}/row_count"
        seperator = 2
        search_tab, charts_tab = st.tabs(['Search', 'Charts'])
        with search_tab:
            logger.log(f"action:load, element:search_tab",flag=4, name=method_name)
            
            ### 검색 기록 받아오기
            endpoint_history = f"{url}/history"
            search_history = get_search_history(endpoint_history, logger)
            if search_history is None or search_history.empty:
                search_history = pd.DataFrame()
            seperator = 3
            top_col1, top_col2 = st.columns([1, 9])
            
            ### dataframe을 보여줄 때 어떤 column을 보여줄지 선택하기 위한 expander
            with top_col1:
                search_filter_expander = st.expander("검색 옵션 표시 :material/search:")
                logger.log(f"action:load, element:checkbox_expander",flag=4, name=method_name)
            seperator = 4

            with search_filter_expander:
                ### expander를 열 경우, filter를 생성해 시각화
                display_filters(logger=logger, search_history=search_history, config=config)
                
            
            ### 필터 옵션 표시 여부
            with top_col2:
                # st.session_state['job_info_filtered'] = False
                col1, col2 = st.columns([8,2])
                with col1:
                    st.subheader("전체 데이터")
                with col2:
                    job_infos_view_count = st.select_slider("한 페이지에 보려는 공고의 수",options=[10,25,50,100]) # number of rows to show in each page, default = 10
                
                ### 총 row 수를 한 페이지에 특정 수로만 보여줌. 각각 tab으로 분리.
                total_row_count = get_table_row_counts(logger, endpoint_row_count, database, table) # total number of rows
                
                # 페이지 탭 생성
                display_paginated_dataframe(logger=logger, config=config, row_count=total_row_count, rows_per_page=job_infos_view_count, is_filtered=False, search_terms=None, visible_columns=visible_columns, data_load_state=data_load_state)
                
                seperator = 12

        with charts_tab:
            ### 데이터를 시각화하기 위한 차트
            logger.log(f"action:load, element:charts_tab",flag=4, name=method_name)
            
            ### select type of chart to show
            chart_type = st.selectbox("Select chart type", ("Pie Chart", "Donut Chart", "Bar Chart", "Horizontal Bar Chart", "Histogram"))
            seperator = 13
            
            ### convert stacks to df to visualize counts
            dev_stacks = get_dev_stacks(_logger=logger, endpoint=f"{config.get('API_URL')}/dev_stacks", database=config.get('DATABASE'))
            stack_counts = Counter(dev_stacks)
            seperator = 14
            
            ### col1 = selected chart, col2 = df of tech stacks with ['stack name', 'count of stacks'] as columns
            col1, col2 = st.columns([2, 1])
            with col1:
                seperator = 15
                if chart_type == "Pie Chart":
                    plot_pie_chart(stack_counts, logger)
                elif chart_type == "Donut Chart":
                    plot_donut_chart(stack_counts, logger)
                elif chart_type == "Bar Chart":
                    plot_bar_chart(stack_counts, logger)
                elif chart_type == "Horizontal Bar Chart":
                    plot_horizontal_bar_chart(stack_counts, logger)
                elif chart_type == "Histogram":
                    plot_histogram(stack_counts, logger)
            with col2:
                seperator = 16
                st.subheader("Tech Stack List")
                stack_df = pd.DataFrame(stack_counts.items(), columns=['Stack', 'Count'])
                logger.log(f"action:load, element:tech_stacks_dataframe",flag=4, name=method_name)
                st.dataframe(stack_df)
        
    except Exception as e:
        logger.log(f"Exception occurred while rendering job informations at #{seperator}: {e}", flag=1, name=method_name)