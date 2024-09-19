import streamlit as st
import pandas as pd
import json, requests, ast
from datetime import datetime
from .utils import Logger

def load_config(config_path:str='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)
    
### clear search history from endpoint
def clear_search_history(endpoint:str, logger)->bool:
    '''
        Clear search history from the endpoint
        - endpoint: API endpoint
        - logger: logger to log the exception
    '''
    method_name = __name__+".clear_search_history"
    is_logged_in = st.session_state.get('connected', False)
    session_id = st.session_state.get('session_id', None)
    user_id = st.session_state.get('user_id', "")
    if is_logged_in:
        if user_id is None or user_id == "":
            logger.log("No user id found", name=method_name, flag=1)
            return False
    if session_id is None:
        logger.log("No session id found", name=method_name, flag=1)
        return False
    payload = {
        "session_id": session_id,
        "user_id": user_id,
        "is_logged_in": is_logged_in
    }
    try:
        clear_response = requests.delete(endpoint, json=payload)
        return clear_response.status_code == 200
    except Exception as e:
        logger.log(f"Exception occurred while clearing search history: {e}", name=method_name, flag=1)
        return False

### retrieve search history from endpoint as dataframe
def get_search_history(endpoint:str, logger)->pd.DataFrame:
    '''
        Get search history from the endpoint
        - endpoint: API endpoint
        - session_id: session id to get search history
        - logger: logger to log the exception
    '''
    method_name = __name__ + ".get_search_history"
    session_id = st.session_state['session_id']
    user_id = st.session_state.get('user_id', "")
    is_logged_in = st.session_state.get('connected', False)
    # @app.get("/history")
    # async def get_search_history(session_id:str, user_id:str, is_logged_in:bool)->list:
    
    history_response = requests.get(endpoint, params={"session_id":session_id, "user_id":user_id, "is_logged_in":is_logged_in})
    # result is serialized dataframe
    # check if result is not empty and status code is 200
    if history_response.status_code == 200 and history_response.text:
        if is_logged_in and user_id is None:
            logger.log("No user id found", name=method_name, flag=1)
            return None
        elif not is_logged_in and session_id is None:
            logger.log("No session id found", name=method_name, flag=1)
            return None
            # deserialize dataframe
        return pd.DataFrame(json.loads(history_response.text))
    else:
        logger.log(f"Exception occurred while retrieving search history: {history_response}", flag=1, name=method_name)
        return None
    
### filter search history
def filter_search_history(search_history:pd.DataFrame, logger:Logger, connected:bool=False)->pd.DataFrame:
    '''
        Filter search history with connected status.
        If connected is False, return search history according to the session id.
        If connected is True, return according to user_id.
        - search_history: search history to filter
        - logger: logger to log the exception
        - connected: connected status
    '''
    method_name = __name__ + ".filter_search_history"
    if connected:
        ## if connected, return search history according to user_id
        return search_history[search_history['user_id'] == st.session_state['user_id']]
    else:
        ## if not connected, return search history according to session_id
        return search_history[search_history['session_id'] == st.session_state['session_id']]
        
### save search history to endpoint and return status as boolean
def save_search_history(endpoint:str, search_history:dict, logger)->requests.Response:
    '''
        Save search history to the endpoint
        - endpoint: API endpoint
        - search_history: search history to save
        - logger: logger to log the exception
    '''
    method_name = __name__ + ".save_search_history"
    try:
        payloads = {
            "session_id": st.session_state['session_id'],
            "search_history": search_history,
            "timestamp": datetime.now().isoformat(),
            "user_id": st.session_state.get('user_id', ""),
            "is_logged_in": st.session_state.get('connected', False),
        }
        save_history_response = requests.post(endpoint, json=payloads)
        return save_history_response
    except Exception as e:
        logger.log(f"Exception occurred while saving search history: {e}", flag=1, name=method_name)
        return False

### retrieve dataframe from endpoint
@st.cache_data
def call_dataframe(_logger, endpoint:str, database:str, query:str)->pd.DataFrame:
    '''
        Send query as post method to the endpoint, and return query results in pandas dataframe format.
        - endpoint: API endpoint
        - database: database name to use
        - query: sql query to execute in database
    '''
    method_name = __name__ + ".call_dataframe"
    try:
        payload = {"database":f"{database}", "query":f"{query}"}
        response = requests.post(endpoint, data=json.dumps(payload))
        if response.status_code==200:
            query_result = json.loads(response.text)
            df = pd.DataFrame(query_result)
            return df
        else:
            _logger.log(f"API Call returned status code {response.status_code}", flag=1, name=method_name)
            return None
    except Exception as e:
        _logger.log(f"Exception occurred while getting dataframe: {e}", flag=1, name=method_name)
        return None
    
def get_dev_stacks(_logger, endpoint:str, database:str)->dict:
    '''
        request dev stacks as {did:count} form.
        - endpoint: API endpoint
        - database: name of database to use
        - table: name of table to use
        - column: name of column to parse.
    '''
    return {}

### retrieve unique values from given column
def get_unique_column_values(_logger, endpoint:str, database:str, table:str, column:str, is_stacked:bool)->list:
    '''
        request unique values in dict to endpoint and return list of values.
        - endpoint: API endpoint
        - database: name of database to use
        - table: name of table to use
        - column: name of column to parse.
    '''
    method_name = __name__ + ".get_unique_column_values"
    try:
        payload = {"database":f"{database}", "table":f"{table}","column":f"{column}","is_stacked":is_stacked}
        result = json.loads(requests.post(endpoint, data=json.dumps(payload)).text)
        return result['unique_values']
    except Exception as e:
        _logger.log(f"Exception occurred while getting unique values for column {column}: {e}", flag=1, name=method_name)
        return None

### retrieve column names of table in database
@st.cache_data
def get_column_names(_logger, endpoint:str, database:str, table:str)->list:
    '''
        request metadata of column names of given table to endpoint
        - endpoint: API endpoint
        - database: name of database to use
        - table: name of table to retrieve columns
    '''
    method_name = __name__ + ".get_column_names"
    try:
        payload = {"database":f"{database}", "table":f"{table}"}
        result = json.loads(requests.post(endpoint, data=json.dumps(payload)).text)
        return result["column_names"]
    except Exception as e:
        _logger.log(f"Exception occurred while getting column names from table {table}: {e}", flag=1, name=method_name)
        return None

### get row count of a table   
def get_table_row_counts(_logger, endpoint:str, database:str, table:str, search_terms:dict=None)->int:
    method_name = __name__ + ".get_table_row_counts"
    try:
        if not search_terms:
            # row count
            query = f"SELECT COUNT(*) FROM {table}"
            payload = {"database":database, "query":query}
            response = requests.post(endpoint, data=json.dumps(payload))
            # check if result is not empty and status code is 200
            if response.status_code == 200 and response.text:
                result = json.loads(response.text)
                return int(result['row_count'])
        else:
            query = f"SELECT COUNT(*) FROM {table} WHERE "
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
                query = f"SELECT COUNT(*) FROM {table}"
            payload = {"database":database, "query":query}
            response = requests.post(endpoint, data=json.dumps(payload))
            if response.status_code == 200 and response.text:
                result = json.loads(response.text)
                return int(result['row_count'])
    except Exception as e:
        _logger.log(f"Exception occurred while counting rows from table {table}: {e}", flag=1, name=method_name)
        return None

def get_dev_stacks(_logger, endpoint:str, database:str)->list:
    method_name = __name__ + ".get_dev_stacks"
    try:
        response = requests.get(endpoint, params={"database":database})
        if response.status_code == 200 and response.text:
            result = json.loads(response.text)
            return list(result['dev_stacks'])
        else:
            _logger.log(f"wrong response from given endpoint: {response.status_code}",flag=1, name=method_name)
            return None
    except Exception as e:
        _logger.log(f"Exception occurred while getting dev stacks: {e}", flag=1, name=method_name)
        return None

def call_stacked_columns(_logger, endpoint:str, database:str, table:str)->list:
    method_name = __name__ + ".call_stacked_columns"
    try:
        response = requests.get(endpoint, params={"database":database, "table":table})
        if response.status_code == 200 and response.text:
            result = json.loads(response.text)
            return list(result['stacked_columns'])
        else:
            _logger.log(f"wrong response from given endpoint: {response.status_code}",flag=1, name=method_name)
            return None
    except Exception as e:
        _logger.log(f"Exception occurred while getting list of stacked columns from table {table}: {e}", flag=1, name=method_name)
        return None
    
def get_elements_from_stacked_element(logger:Logger, df:pd.DataFrame, column:str)->list:
    all_elems = []
    for row in df[column]:
        try:
            col_elem_list = ast.literal_eval(row)
        except (SyntaxError, ValueError) as e:
            logger.log(f"Error parsing row: {row}, error: {e}", flag=1, name=method_name)
            continue
        all_elems.extend(col_elem_list)
    result = list(set(all_elems))
    return result