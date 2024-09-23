import ast
import streamlit as st
import pandas as pd
import json, math, os
import matplotlib.pyplot as plt
from collections import Counter
from .utils import Logger
from datetime import datetime
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
        dev_stacks = job_information['dev_stacks'] # list
        start_date = job_information['start_date'] # datetime
        end_date = job_information['end_date'] # datetime
        crawl_url = job_information['crawl_url']
        get_date = job_information['get_date'] # datetime
        required_career = job_information['required_career'] # bool
        job_prefer = job_information['job_prefer'] # list
        st.markdown(f"# [{company_name}]({crawl_url})")
        gd_obj = datetime.strptime(get_date, "%Y-%m-%dT%H:%M:%S")
        g_year = gd_obj.year
        g_month = gd_obj.month
        g_day = gd_obj.day
        g_hour = gd_obj.hour
        g_min = gd_obj.minute
        st.markdown(f"공고 개시 일자:{g_year}-{g_month}-{g_day} {g_hour}:{g_min}")
        if required_career:
            st.markdown(f" 경력직 여부: :material/check_box:")
        else:
            st.markdown(f" 경력직 여부: :material/check_box_outline_blank:")
        st.markdown(f"## {job_title}")
        if len(dev_stacks) > 0:
            st.markdown(f"### 요구 스택")
        for stack in dev_stacks:
            st.markdown(f"- {stack}")
        if len(job_prefer) > 0:
            st.markdown(f"### 우대 사항")
        for prefer in job_prefer:
            st.markdown(f"- {prefer}")
            
        st.markdown(f"### 공고 모집 일자")
        if start_date:
            sd_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
            s_year = sd_obj.year
            s_month = sd_obj.month
            s_day = sd_obj.day
            s_hour = sd_obj.hour
            s_min = sd_obj.minute
            st.markdown(f"- 시작일: {s_year}-{s_month}-{s_day} {s_hour}:{s_min}")
        else:
            st.markdown(f"- ~~시작일:~~")
            
        if end_date:
            ed_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")
            e_year = ed_obj.year
            e_month = ed_obj.month
            e_day = ed_obj.day
            e_hour = ed_obj.hour
            e_min = ed_obj.minute
            st.markdown(f"- 마감일: {e_year}-{e_month}-{e_day} {e_hour}:{e_min}")
        else:
            st.markdown(f"- ~~마감일:~~")
        
        if start_date or end_date:
            st.markdown(f"- 상시모집 여부: :material/check_box_outline_blank:")
        else:
            st.markdown(f"- 상시모집 여부: :material/check_box:")

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
                    dev_stacks = job_information['dev_stacks'] # datetime
                    start_date = job_information['start_date'] # datetime
                    end_date = job_information['end_date'] # datetime
                    crawl_url = job_information['crawl_url']
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
                        sd_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S")
                        s_year = sd_obj.year
                        s_month = sd_obj.month
                        s_day = sd_obj.day
                        s_hour = sd_obj.hour
                        s_min = sd_obj.minute
                        date_text = f"{s_year}-{s_month}-{s_day} {s_hour}:{s_min}"
                    if end_date:
                        ed_obj = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S")
                        e_year = ed_obj.year
                        e_month = ed_obj.month
                        e_day = ed_obj.day
                        e_hour = ed_obj.hour
                        e_min = ed_obj.minute
                        date_text += f" ~ {e_year}-{e_month}-{e_day} {e_hour}:{e_min}"
                    if date_text == "":
                        date_text = "상시모집"
                    st.write(date_text)
                with col2:
                    if st.button("자세히 보기", key=pid):
                        detail(logger, pid)
                    st.link_button('공고 보기', url=crawl_url)
                
    except Exception as e:
        logger.log(f"Exception occurred while rendering home page: {e}", flag=1, name=method_name)