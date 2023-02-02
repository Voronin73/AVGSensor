DB_POLIGON_USER = 'meteocube_level1'
DB_POLIGON_PASSWD = 'user4d'
DB_POLIGON_HOST = '192.168.2.220'
DB_POLIGON_PORT = 5432
DB_POLIGON_NAME = 'meteocube'
znk = 3    # Округление, количесво знаков после запятой

"""SQL"""

measurand_winds_label = [['ws_ins', 'wd_ins']]  # Первое значение скорости, второе направление

measurand_labels_not_avg = ['prs_fct']
sql_label_pattern = "label like '{LABEL_MEASURAND}'"

sql_no_mesurand_pattern = "and measurand_id != {NOT_MEASURAND} and "

sql_condition_sensors = "(time_obs between '{TIME_BEGIN}' and '{TIME_END}') {NOT_MEASURAND}" \
             "(array_position(value_float, NULL) is null and value_float is not null)"

sql_value_pattern = "({SOURCE_ID}, {MEASURAND_ID},'{TIME_OBS}','{TIME_REC}','{{{VALUE}}}')"
sql_value_insert_pattern = "insert into {TABLE} ({PARAMETERS}) values ({VALUES})"

