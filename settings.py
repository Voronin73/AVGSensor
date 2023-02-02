DB_POLIGON_USER = 'meteocube_level1'
DB_POLIGON_PASSWD = 'user4d'
DB_POLIGON_HOST = '192.168.2.220'
DB_POLIGON_PORT = 5432
DB_POLIGON_NAME = 'meteocube'
znk = 3    # Округление, количесво знаков после запятой

"""Measurands"""

measurand_winds_label = [['ws_ins', 'wd_ins']]  # Первое значение скорости, второе направление

measurand_labels_not_avg = ['prs_fct']          # Не используеиые

"""SQL"""
"Table"
scheme_data = 'meteo_point'
scheme_info = 'info'
table_in_data = 'sensor'
teble_out_data = ''
table_measurand = 'measurand'

table_request_sensor = f'{scheme_data}.{table_in_data} join {scheme_info}.{table_measurand} on ' \
                       f'{scheme_data}.{table_in_data}.measurand_id = {scheme_info}.{table_measurand}.id'

sql_label_measurands = "label {NOT} like '{LABEL_MEASURAND}'"

sql_parameter_no_wind = "source_id::varchar(255), label, min(value_float[1]), max(value_float[1]), " \
                        "round(avg(value_float[1])::numeric, {znk})::float".format(znk=znk)

sql_parameter_wind = "source_id::varchar(255), label, array_agg(value_float[1])"

sql_condition_sensors = "(time_obs between '{TIME_BEGIN}' and '{TIME_END}') and {MEASURAND} " \
                        " value_float is not null and value_float[1] is not null " \
                        "group by source_id, label having count(value_float) != 0;"

sql_value_pattern = "({SOURCE_ID}, {MEASURAND_ID},'{TIME_OBS}','{TIME_REC}','{{{VALUE}}}')"
sql_value_insert_pattern = "insert into {TABLE} ({PARAMETERS}) values ({VALUES})"


