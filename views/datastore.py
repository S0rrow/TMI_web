import json, requests
from .utils import Logger

def load_config(config_path:str='config.json')->dict:
    with open(config_path, 'r') as f:
        return json.load(f)

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

def call_pid_list(_logger:Logger, search_keyword:str="")->list:
    method_name = __name__ + ".call_pid_list"
    try:
        config = load_config()
        endpoint = config.get('API_URL') + "/search_keyword"
        response = requests.get(endpoint, params={'database':config.get('DATABASE'), 'search_keyword':search_keyword})
        if response.status_code==200 and response.text:
            result = json.loads(response.text)
            return list(result['result'])
        else:
            _logger.log(f"wrong response from given endpoint:{response.status_code}",flag=1,name=method_name)
    except Exception as e:
        _logger.log(f"Exception occurred while getting pid list for given search keyword:{e}", flag=1, name=method_name)
        return None

def call_job_informations(_logger:Logger, pid_list:list)->dict:
    method_name = __name__ + ".call_job_informations"
    try:
        config = load_config()
        endpoint = config.get('API_URL') + "/job_information"
        response = requests.get(endpoint ,params={'database':config.get('DATABASE'), 'pid_list':str(pid_list)})
        if response.status_code==200 and response.text:
            result = json.loads(response.text)
            return result
        else:
            _logger.log(f"wrong response from given endpoint:{response.status_code}",flag=1,name=method_name)
    except Exception as e:
        _logger.log(f"Exception occurred while getting job informations for given pid list:{e}", flag=1, name=method_name)
        return None