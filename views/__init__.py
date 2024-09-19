from views.home import display_home_page
from views.job_informations import display_job_informations
from views.login import display_login_page
from views.user_information import display_user_information
from views.error import display_error_page
from views.history import display_history
from views.utils import Logger
from views.datastore import call_dataframe, get_search_history, save_search_history, load_config, get_unique_column_values, get_column_names, get_table_row_counts, call_stacked_columns, get_elements_from_stacked_element