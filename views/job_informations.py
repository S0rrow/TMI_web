import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
from collections import Counter
from .utils import Logger
from .datastore import call_dataframe, get_search_history, save_search_history, load_config, get_unique_column_values, get_column_names, get_table_row_counts, get_stacked_columns

### dialog
@st.dialog("Detailed Information", width="large")
def detail(logger:Logger, config, pid, crawl_url):
    method_name = __name__ + ".detail"
    try:
        url = config.get('API_URL')
        database = config.get('DATABASE')
        query = f"SELECT * FROM your_table WHERE pid = {pid} AND crawl_url = '{crawl_url}';"
        row_df = call_dataframe(logger, endpoint=f"{url}/query", database=database, query=query)
        st.dataframe(row_df, use_container_width=True)
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
def display_filters(logger:Logger, search_history:pd.DataFrame, columns_to_visualize:dict, config) -> dict:
    '''
    Generate filters for each column in the dataframe.
    - df: dataframe to filter
    - search_history: dataframe to store search history
    '''
    method_name = __name__ + ".display_filters"
    visible_columns = [col for col, show in columns_to_visualize.items() if show]
    num_visible_columns = len(visible_columns)  # True인 열의 개수 저장
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
    seperator = 1
    try:
        # Divide columns into equal widths to display filters horizontally
        #num_columns = len(df.columns)  # Number of columns to filter
        # logger.log(f"num_visible_columns:{num_visible_columns}", flag=0, name=method_name)
        if num_visible_columns <= 0:
            logger.log(f"No columns to show", flag=0, name=method_name)
            st.write("No columns selected")
            return latest_search_term
        # api에서 stack형 column의 목록을 호출
        stacked_columns = get_stacked_columns(_logger=logger, endpoint=f"{config.get('API_URL')}/stacked_columns", database=config.get('DATABASE'), table=config.get('TABLE'))
        # logger.log(f"stacked_column_list:{stacked_columns}", flag=0, name=method_name)
        # api에서 모든 column의 목록을 호출
        total_columns = get_column_names(_logger=logger, endpoint=f"{config.get('API_URL')}/columns", database=config.get('DATABASE'), table=config.get('TABLE'))
        columns = st.columns(num_visible_columns)  # Create column containers
        i = 0
        seperator = 3
        for column in total_columns:
            with columns[i]:
                is_stacked = column in stacked_columns
                # logger.log(f"column name:{column}, is_stacked:{is_stacked}",flag=0, name=method_name)
                unique_values = get_unique_column_values(logger, endpoint=f"{config.get('API_URL')}/unique_values", database=config.get('DATABASE'), table=config.get('TABLE'), column=column,is_stacked=is_stacked)
                
                seperator = 4
                if st.session_state['apply_last_filter']:
                    default_filter = latest_search_term.get(column, [])
                else:
                    default_filter = []
                logger.log(f"default_filter:{default_filter}", flag=0, name=method_name)
                selected_stacks = st.multiselect(f"{column}", unique_values, default=default_filter)
                
                if selected_stacks:
                    latest_search_term[column] = selected_stacks
                if i < num_visible_columns:
                    i += 1
        seperator = 5
        logger.log(f"action:load, element:search_filters", flag=4, name=method_name)
        return latest_search_term

    except Exception as e:
        logger.log(f"Exception occurred while displaying filters at seperator #{seperator}: {e}", flag=1, name=method_name)
        return latest_search_term

def generate_dataframe(logger:Logger, config:dict, search_terms:dict, is_filtered:bool, data_load_state)->pd.DataFrame:
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
    else:
        query = f"SELECT * FROM {table}"
    url = config.get('API_URL')
    endpoint_query = f"{url}/query"
    try:
        df = call_dataframe(logger, endpoint_query, database, query)
        if df.empty or df is None:
            logger.log(f"dataframe is empty: {e}", flag=0, name=method_name)
            data_load_state.text("No data found.")
            return None
        data_load_state.text("Data loaded from st.cached_data")
        return df
    except Exception as e:
        data_load_state.text(f"Failed to load data: {e}")
        logger.log(f"Excpetion occurred while generating dataframe: {e}", flag=1, name=method_name)
        return None

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
        column_length = get_table_row_counts(logger, endpoint_row_count, database, table)
        seperator = 2

        ### 검색 기록 받아오기
        endpoint_history = f"{url}/history"
        search_history = get_search_history(endpoint_history, logger)
        if search_history is None or search_history.empty:
            search_history = pd.DataFrame()
        seperator = 3
        
        top_col1, top_col2 = st.columns(2)
        ### dataframe을 보여줄 때 어떤 column을 보여줄지 선택하기 위한 expander
        with top_col1:
            checkbox_expander = st.expander("표시할 열(Column)을 선택하세요")
        default_visualized_column_list = {}
        columns_to_visualize = {}
        seperator = 4
        
        ### default를 보여주도록 설정되어 있을 경우
        # logger.log(f"total_columns:{total_columns}",flag=0,name=method_name)
        for column in total_columns:
            if column in ['job_title', 'job_categories', 'end_date', 'crawl_domain', 'company_name', 'start_date']:
                default_visualized_column_list[column] = True
                columns_to_visualize[column] = True
            else:
                default_visualized_column_list[column] = False
                columns_to_visualize[column] = False
        show_default_columns = st.session_state.get('show_default_columns', False)
        seperator = 5
        
        ### 선택을 수정한 기록이 있을 경우
        if 'column_list_to_visualize' not in st.session_state:
            st.session_state['column_list_to_visualize'] = columns_to_visualize

        with checkbox_expander:
            ### expander를 실제로 열었을 경우 각 checkbox들이 선택되면 값을 True로 변경.
            if show_default_columns:
                for column in total_columns:
                    value = default_visualized_column_list[column]
                    column_checkbox = st.checkbox(f"{column}", value=value, key=column)
                    if column_checkbox:
                        st.session_state['column_list_to_visualize'][column] = True
                    else:
                        st.session_state['column_list_to_visualize'][column] = False
            else:
                for column in total_columns:
                    if st.checkbox(f"{column}", value=True):
                        st.session_state['column_list_to_visualize'][column] = True
        
        ### 필터 옵션 표시 여부
        with top_col2:
            show_filters = st.checkbox("필터 옵션 표시", value=False)
            logger.log(f"action:load, element:checkbox_enable_search_filters",flag=4, name=method_name)
        seperator = 6
        
        visible_columns = [col for col, show in st.session_state['column_list_to_visualize'].items() if show]
        
        if show_filters:
            ### 필터를 보여주도록 선택한 경우
            logger.log(f"action:click, element:checkbox_enable_search_filters",flag=4, name=method_name)
            current_filter = display_filters(logger, search_history, st.session_state['column_list_to_visualize'], config)
            filter_btn = st.button("필터 적용")
            logger.log(f"action:load, element:apply_filter_button",flag=4, name=method_name)
            reset_filter_btn = st.button("필터 초기화")
            logger.log(f"action:load, element:reset_filter_button",flag=4, name=method_name)
            seperator = 7
            col1, col2 = st.columns([2, 1])
            with col1:
                if filter_btn:
                    logger.log(f"action:click, element:apply_filter_button",flag=4, name=method_name)
                    st.session_state['job_info_filtered'] = True
                    # 필터 로그 저장
                    save_history_response = save_search_history(endpoint_history, current_filter, logger)
                    if save_history_response.status_code == 200 and save_history_response.json().get("status") == "success":
                        st.success("필터가 저장되었습니다.")
                        st.session_state['apply_last_filter'] = True
                    else:
                        st.error(f"필터 저장에 실패했습니다. ({save_history_response.status_code})")
                        st.session_state['apply_last_filter'] = False
                    seperator = 8
            with col2:
                if reset_filter_btn:
                    st.session_state['job_info_filtered'] = False
                    logger.log(f"action:click, element:reset_filter_button",flag=4, name=method_name)
                    st.session_state['apply_last_filter'] = False
                    st.success("필터가 초기화되었습니다.")
                    st.rerun()
            seperator = 9

            # 필터링된 데이터프레임 표시. 단, filter_btn이 눌리지 않았을 때는 이전의 df 유지
            search_result_state = st.subheader("검색 결과")
            if st.session_state.get('job_info_filtered', False):
                ### 버튼이 눌렸을 경우, 최종적으로 필터링된 데이터프레임 시각화
                seperator = 10
                result_df = generate_dataframe(logger, config, search_terms=current_filter, is_filtered=True, data_load_state=data_load_state)
                
                for index, row in result_df.iterrows():
                    col1, col2 = st.columns([10,1])
                    sliced_row_df = pd.DataFrame(row.loc[visible_columns])
                    row_df = pd.DataFrame(row)
                    with col1:
                        st.table(data=sliced_row_df.transpose())
                    with col2:
                        detail_btn = st.button(f"자세히 보기", key=index)
                        if detail_btn:
                            detail(row_df, logger)
            else:
                ### 버튼이 눌리지 않았을 경우
                result_df = pd.DataFrame()
                st.write("No search term applied")
            
        else:
            seperator = 11
            st.session_state['job_info_filtered'] = False
            st.subheader("전체 데이터")
            #filtered_visualized_df = df.loc[:, visible_columns]
            result_df = generate_dataframe(logger, config=config, search_terms=None, is_filtered=False, data_load_state=data_load_state)
            
            ### 필터가 없는 경우 전체 데이터프레임에서 특정 열만 선택해 시각화
            for index, row in result_df.iterrows():
                col1, col2 = st.columns([10,1])
                sliced_row_df = pd.DataFrame(row.loc[visible_columns])
                row_df = pd.DataFrame(row)
                with col1:
                    st.table(data=sliced_row_df.transpose())
                with col2:
                    detail_btn = st.button(f"자세히 보기", key=index)
                    if detail_btn:
                        detail(row_df, logger)
            seperator = 12
        
        ### 데이터를 시각화하기 위한 차트
        
        ### select type of chart to show
        chart_type = st.selectbox("Select chart type", ("Pie Chart", "Donut Chart", "Bar Chart", "Horizontal Bar Chart", "Histogram"))
        seperator = 13
        
        ### convert stacks to df to visualize counts
        dev_stacks = get_unique_column_values(logger, endpoint=f"{config.get('API_URL')}/unique_values",database=config.get('DATABASE'), table=config.get('TABLE'), column="dev_stacks",is_stacked=True)
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