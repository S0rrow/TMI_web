import ast
import streamlit as st
import pandas as pd
import json, math, os
import matplotlib.pyplot as plt
from collections import Counter
from .utils import Logger
from .datastore import load_config, call_pid_list, call_job_informations

### dialog
@st.dialog("세부 정보", width="large")
def detail(logger:Logger, pid:int):
    method_name = __name__ + ".detail"
    logger.log(f"action:load, element:detail_page_{pid}",flag=4, name=method_name)
    try:
        pid_list = []
        pid_list.append(pid)
        job_information = call_job_informations(logger, pid_list)[pid]
        job_title = job_information['job_title']
        company_name = job_information['company_name']
        dev_stacks = job_information['dev_stacks']
        start_date = job_information['start_date']
        end_date = job_information['end_date']
        st.markdown(f"## {company_name}")
        st.markdown(f"### {job_title}")
        if len(dev_stacks) > 0:
            if len(dev_stacks) > 8:
                dev_stacks_to_show = dev_stacks[:8]
                dev_stacks_to_show.append("...")
            else:
                dev_stacks_to_show = dev_stacks
            dev_stack_cols = st.columns(len(dev_stacks_to_show))
            for dindex, stack in enumerate(dev_stacks_to_show):
                with dev_stack_cols[dindex]:
                    with st.container(border=True):
                        st.write(stack)
        date_text = ""
        if start_date:
            date_text = f"{start_date}"
        if end_date:
            date_text += f" ~ {end_date}"
        if date_text == "":
            date_text = "상시모집"
        st.write(date_text)

    except Exception as e:
        st.write(f"Exception:{e}")
        logger.log(f"Exception occurred while getting detailed dataframe from api: {e}", flag=1, name=method_name)

def display_home_page(logger:Logger):
    '''
    show initial page before login
    '''
    method_name = __name__ + ".display_home_page"
    try:
        config = load_config()
        
        ### title
        st.title("Home")
        
        ### sidebar
        with st.sidebar:
            search_expander = st.expander("검색 :material/search:")
        with search_expander:
            search_keyword = st.text_input("검색할 키워드를 입력하세요")
            se_col1, se_col2 = st.columns(2)
            with se_col1:
                search_btn = st.button("검색", use_container_width=True)                
                if search_btn:
                    st.session_state['is_filtered'] = True
            with se_col2:
                reset_btn = st.button("초기화", use_container_width=True)
                if reset_btn:
                    st.session_state['is_filtered'] = False

        ### pid list resulted for search option. by default, search all.
        if st.session_state.get('is_filtered', False):
            pid_list = call_pid_list(logger, search_keyword)
        else:
            pid_list = call_pid_list(logger)
        
        total_row = len(pid_list) # number of pids
        data_load_status = st.text(f"{total_row}개의 공고가 발견되었습니다.")
        
        ### paginator
        top_col1, top_col2 = st.columns([8, 2])
        with top_col1:
            rows_per_page = st.select_slider("한 페이지에 보려는 공고의 수", options=[10,25,50,100])
            
        num_pages = math.ceil(total_row / rows_per_page) # number of pages
        with top_col2:
            page = st.selectbox("페이지", options=[i+1 for i in range(num_pages)])
        page_fix = page-1
        offset = page_fix * rows_per_page
        # row를 몇개까지 출력할지
        limit = rows_per_page if (offset + rows_per_page) <= total_row else total_row - offset
        results = pid_list[offset:offset + limit]
        job_informations = call_job_informations(logger, results)
        for pid in results:
            ### 각 채용 공고 세부 정보
            row_container = st.container(height=400, border=True)
            with row_container:
                col1, col2 = st.columns([9,1])
                with col1:
                    job_information = job_informations[pid]
                    job_title = job_information['job_title']
                    company_name = job_information['company_name']
                    dev_stacks = job_information['dev_stacks']
                    start_date = job_information['start_date']
                    end_date = job_information['end_date']
                    st.markdown(f"## {company_name}")
                    st.markdown(f"### {job_title}")
                    if len(dev_stacks) > 0:
                        if len(dev_stacks) > 8:
                            dev_stacks_to_show = dev_stacks[:8]
                            dev_stacks_to_show.append("...")
                        else:
                            dev_stacks_to_show = dev_stacks
                        dev_stack_cols = st.columns(len(dev_stacks_to_show))
                        for dindex, stack in enumerate(dev_stacks_to_show):
                            with dev_stack_cols[dindex]:
                                with st.container(border=True):
                                    st.write(stack)
                    date_text = ""
                    if start_date:
                        date_text = f"{start_date}"
                    if end_date:
                        date_text += f" ~ {end_date}"
                    if date_text == "":
                        date_text = "상시모집"
                    st.write(date_text)
                with col2:
                    if st.button("자세히 보기", key=pid):
                        detail(logger, pid)
                
    except Exception as e:
        logger.log(f"Exception occurred while rendering home page: {e}", flag=1, name=method_name)