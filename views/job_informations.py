import streamlit as st
import pandas as pd
import json, requests, ast, base64
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
from .utils import Logger
from .datastore import get_job_informations, get_search_history, save_search_history, load_config

### dialog
@st.dialog("Detailed Information", width="large")
def detail(row_df:pd.DataFrame, logger:Logger):
    st.write(row_df.transpose().columns.tolist())
    st.table(row_df.transpose())

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
def display_filters(df: pd.DataFrame, search_history: pd.DataFrame, logger:Logger, columns_to_visualize:dict) -> pd.DataFrame:
    '''
    Generate filters for each column in the dataframe.
    - df: dataframe to filter
    - search_history: dataframe to store search history
    '''
    method_name = __name__ + ".display_filters"
    visible_columns = [col for col, show in columns_to_visualize.items() if show]
    num_visible_columns = len(visible_columns)  # True인 열의 개수 저장
    
    # Get the latest search term for the current session
    if search_history is not None and not search_history.empty:
        if len(search_history) == 1:
            latest_search_term = json.loads(search_history.iloc[0]['search_term'])
        else:
            latest_search_term = json.loads(search_history.iloc[-1]['search_term'])
    else:
        latest_search_term = {}

    if df.empty or df is None:
        logger.log(f"Dataframe is empty", flag=1, name=method_name)
        return None, latest_search_term
    else:
        filtered_df = df.copy()

    try:
        # Divide columns into equal widths to display filters horizontally
        #num_columns = len(df.columns)  # Number of columns to filter
        logger.log(f"num_visible_columns:{num_visible_columns}", flag=0, name=method_name)
        columns = st.columns(num_visible_columns)  # Create column containers
        i = 0
        for column in df.columns:
            with columns[i]:  # Render each filter within its own column   
                ### if column is 'stacks', show unique stacks in multiselect
                if column == 'stacks' and columns_to_visualize[column]:
                    all_stacks = []
                    for stack in df['stacks']:
                        stack_list = ast.literal_eval(stack)
                        all_stacks.extend(stack_list)
                    unique_stacks = list(set(all_stacks))
                    
                    if st.session_state.get('apply_last_filter', None):
                        default_filter = latest_search_term.get(column, [])
                    else:
                        default_filter = []

                    selected_stacks = st.multiselect(f"{column}", unique_stacks, default=default_filter)
                    
                    if selected_stacks:
                        filtered_df = filtered_df[filtered_df['stacks'].apply(
                            lambda x: any(stack in ast.literal_eval(x) for stack in selected_stacks)
                        )]
                    latest_search_term[column] = selected_stacks
                    i += 1
                ### if column is not 'stacks', show unique values in multiselect
                elif columns_to_visualize[column]:# df[column].dtype == 'object':
                    unique_values = df[column].unique().tolist()
                    if None in unique_values:
                        unique_values = ['None' if v is None else v for v in unique_values]
                    unique_values = sorted(unique_values)
                    
                    if st.session_state['apply_last_filter']:
                        default_filter = latest_search_term.get(column, [])
                    else:
                        default_filter = []

                    selected_values = st.multiselect(f"{column}", unique_values, default=default_filter)

                    if selected_values:
                        if 'None' in selected_values:
                            filtered_df = filtered_df[
                                (filtered_df[column].isin([v for v in selected_values if v != 'None'])) | (filtered_df[column].isna())
                            ]
                        else:
                            filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
                    latest_search_term[column] = selected_values
                    i += 1
        logger.log(f"action:load, element:search_filters", flag=4, name=method_name)
        return filtered_df, latest_search_term

    except Exception as e:
        logger.log(f"Exception occurred while displaying filters: {e}", flag=1, name=method_name)
        return None, latest_search_term



### page display
def display_job_informations(logger, url:str=None, database:str=None, query:str=None):
    '''
        display job informations retreived from given url
    '''
    ### seperator for debug
    seperator = -1
    method_name = __name__ + ".display_job_informations"
    try:
        config = load_config()
        if not url:
            url = config.get("API_URL")
        if not query:
            query = f"SELECT * from {config.get('TABLE')}"
        if not database:
            database = config.get("DATABASE")
        if 'job_info_filtered' not in st.session_state:
            st.session_state['job_info_filtered'] = False
        seperator = 0
        st.title("Job Information - Tech Stack Visualizations")
        logger.log(f"action:load, element:title",flag=4, name=method_name)
        st.header("Job Informations")
        logger.log(f"action:load, element:header",flag=4, name=method_name)
        data_load_state = st.text('Loading data...')
        logger.log(f"action:load, element:data_load_state",flag=4, name=method_name)
        seperator = 1
        
        # TODO
        # 현재는 /test
        ### test endpoint로부터 데이터프레임 받아오기
        endpoint_test = f"{url}/query"
        df = get_job_informations(logger, endpoint_test, database, query)
        seperator = 2

        ### 검색 기록 받아오기
        endpoint_history = f"{url}/history"
        search_history = get_search_history(endpoint_history, logger)
        if search_history is None or search_history.empty:
            # logger.log(f"No search history found", flag=1, name=method_name)
            search_history = pd.DataFrame()
        seperator = 3

        ### 데이터가 없을 경우 예외 처리
        if df is None or df.empty:
            st.write("No data found")
            return
        else:
            st.session_state['apply_last_filter'] = True
        visualized_df = df.copy()
        data_load_state.text("Data loaded from st.cached_data")
        seperator = 4
        
        top_col1, top_col2 = st.columns(2)
        ### dataframe을 보여줄 때 어떤 column을 보여줄지 선택하기 위한 expander
        with top_col1:
            checkbox_expander = st.expander("표시할 열(Column)을 선택하세요")
        default_visualized_column_list = {}
        columns_to_visualize = {}
        
        ### default를 보여주도록 설정되어 있을 경우
        for column in visualized_df.columns:
            if column in ['job_title', 'stacks', 'company_name', 'country', 'remote', 'job_category','stacks', 'URL']:
                default_visualized_column_list[column] = True
            else:
                default_visualized_column_list[column] = False
            columns_to_visualize[column] = False
        show_default_columns = st.session_state.get('show_default_columns', False)

        ### 그게 아니라 선택을 수정한 기록이 있을 경우
        if 'column_list_to_visualize' not in st.session_state:
            st.session_state['column_list_to_visualize'] = columns_to_visualize

        with checkbox_expander:
            if show_default_columns:
                for column in visualized_df.columns:
                    value = default_visualized_column_list[column]
                    column_checkbox = st.checkbox(f"{column}", value=value, key=column)
                    if column_checkbox:
                        st.session_state['column_list_to_visualize'][column] = True
                    else:
                        st.session_state['column_list_to_visualize'][column] = False
            else:
                for column in visualized_df.columns:
                    if st.checkbox(f"{column}", value=True):
                        st.session_state['column_list_to_visualize'][column] = True
        
        ### 필터 옵션 표시 여부
        with top_col2:
            show_filters = st.checkbox("필터 옵션 표시", value=False)
            logger.log(f"action:load, element:checkbox_enable_search_filters",flag=4, name=method_name)
        seperator = 6
        
        visible_columns = [col for col, show in st.session_state['column_list_to_visualize'].items() if show]
        
        if show_filters:
            logger.log(f"action:click, element:checkbox_enable_search_filters",flag=4, name=method_name)
            st.session_state['job_info_filtered'] = True
            filtered_df, current_filter = display_filters(df, search_history, logger, columns_to_visualize)
            filter_btn = st.button("필터 적용")
            logger.log(f"action:load, element:apply_filter_button",flag=4, name=method_name)
            reset_filter_btn = st.button("필터 초기화")
            logger.log(f"action:load, element:reset_filter_button",flag=4, name=method_name)
            seperator = 7
            col1, col2 = st.columns([2, 1])
            with col1:
                if filter_btn:
                    logger.log(f"action:click, element:apply_filter_button",flag=4, name=method_name)
                    # 필터 로그 저장
                    ## class SearchHistory(BaseModel):
                    # session_id: str
                    # search_history: dict
                    # timestamp: datetime
                    # user_id: str
                    # is_logged_in: bool
                    save_history_response = save_search_history(endpoint_history, current_filter, logger)
                    if save_history_response.status_code == 200 and save_history_response.json().get("status") == "success":
                        st.success("필터가 저장되었습니다.")
                        st.session_state['apply_last_filter'] = True
                    else:
                        st.error("필터 저장에 실패했습니다.")
                        st.session_state['apply_last_filter'] = False
                    visualized_df = filtered_df.copy()
                    seperator = 8
            with col2:
                if reset_filter_btn:
                    logger.log(f"action:click, element:reset_filter_button",flag=4, name=method_name)
                    st.session_state['apply_last_filter'] = False
                    visualized_df = df.copy()
                    st.success("필터가 초기화되었습니다.")
                    st.rerun()
            seperator = 9

            # 필터링된 데이터프레임 표시. 단, filter_btn이 눌리지 않았을 때는 이전의 df 유지
            st.subheader("필터링된 데이터")
            filtered_visualized_df = visualized_df.loc[:, visible_columns]
            
            ### 최종적으로 필터링된 데이터프레임 시각화
            st.dataframe(filtered_visualized_df, use_container_width=True)
            seperator = 10
        else:
            st.session_state['job_info_filtered'] = False
            st.subheader("전체 데이터")
            filtered_visualized_df = df.loc[:, visible_columns]
            
            ### 필터가 없는 경우 전체 데이터프레임에서 특정 열만 선택해 시각화
            for index, row in df.iterrows():
                col1, col2 = st.columns([10,1])
                sliced_row_df = pd.DataFrame(row.loc[visible_columns])
                row_df = pd.DataFrame(row)
                with col1:
                    st.table(data=sliced_row_df.transpose())
                with col2:
                    detail_btn = st.button(f"자세히 보기", key=index)
                    if detail_btn:
                        detail(row_df, logger)
            #st.dataframe(filtered_visualized_df, use_container_width=True)
            seperator = 11
        
        ### select type of chart to show
        chart_type = st.selectbox("Select chart type", ("Pie Chart", "Donut Chart", "Bar Chart", "Horizontal Bar Chart", "Histogram"))
        seperator = 12
        
        ### convert stacks to df to visualize counts
        all_stacks = []
        if st.session_state['job_info_filtered']:
            for stack in visualized_df['stacks']:
                stack_list = ast.literal_eval(stack)  # string to list
                all_stacks.extend(stack_list)  # combine into single list
        else:
            for stack in df['stacks']:
                stack_list = ast.literal_eval(stack)  # string to list
                all_stacks.extend(stack_list)  # combine into single list
        stack_counts = Counter(all_stacks)
        seperator = 13
        ### col1 = selected chart, col2 = df of tech stacks with ['stack name', 'count of stacks'] as columns
        col1, col2 = st.columns([2, 1])
        with col1:
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
            st.subheader("Tech Stack List")
            stack_df = pd.DataFrame(stack_counts.items(), columns=['Stack', 'Count'])
            logger.log(f"action:load, element:tech_stacks_dataframe",flag=4, name=method_name)
            st.dataframe(stack_df)
        seperator = 14
    except Exception as e:
        logger.log(f"Exception occurred while rendering job informations at #{seperator}: {e}", flag=1, name=method_name)