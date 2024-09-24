import os
import streamlit as st
import views
from views.utils import Logger

logger = views.Logger(options={"name":__name__})

### Button Callback Functions

# Home button
def on_click_home(logger:Logger):
    st.session_state['current_view'] = "home"
    
def on_click_chart(logger:Logger):
    st.session_state['current_view'] = "chart"

def main():
    ### initial configurations
    seperator = -1
    method_name = __name__ + ".main"
    parent_path = os.path.dirname(os.path.abspath(__file__))
    st.logo(f"{parent_path}/images/horizontal.png", icon_image=f"{parent_path}/images/logo.png")
    
    try:
        ### page configuration ###
        seperator = 0
        st.set_page_config(
            page_title="Tech Map IT | Prototype",
            layout='wide', # 'centered' or 'wide'
            page_icon=f"{parent_path}/images/logo.png",
            initial_sidebar_state="auto"
        )
        
        ### current_view init
        seperator = 1
        # if no session_state.current_view exists
        if not st.session_state.get('current_view', False):
            st.session_state['current_view'] = "home"
        
        if not st.session_state.get('is_filtered', False):
            st.session_state['is_filtered'] = False 
        
        ### sidebar configuration
        seperator = 3
        with st.sidebar:
            st.write("Home")
            home_btn = st.button("Home :material/home:", on_click=on_click_home(logger), use_container_width=True)
            chart_btn = st.button("Chart :material/analystics:", on_click=on_click_chart(logger), use_container_width=True)
        logger.log(f"action:load, element:sidebar", flag=4, name=method_name)
        
        
        ### display page according to current_view
        seperator = 4
        if st.session_state.get('current_view') == "home":
            views.display_home_page(logger)
        elif st.session_state.get('current_view') == "chart":
            views.display_chart_page(logger)
    
    except Exception as e:
        logger.log(f"Exception occurred at flag #{seperator}: {e}", flag=1, name=__name__)
        
if __name__=="__main__":
    main()