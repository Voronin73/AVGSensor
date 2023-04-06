DB_POLIGON_USER = 'meteocube_level1'
DB_POLIGON_PASSWD = 'user4d'
DB_POLIGON_HOST = '192.168.2.220'
DB_POLIGON_PORT = 5432
DB_POLIGON_NAME = 'meteocube'
znk = 3    # Округление, количесво знаков после запятой

"""Measurands"""

measurand_winds_label = [['ws_ins', 'wd_ins']]  # Первое значение скорости, второе направление

measurand_labels_not_avg = ['prs_fct']          # Не используеиые

mesurand_label_method_processing_ins = 'ins'    # Мгновенное значение
mesurand_label_method_processing_avg = 'avg'   # Среднее значение
mesurand_label_method_processing_max = 'max'   # Максимальное значение
mesurand_label_method_processing_min = 'min'    # Минимальное значение
mesurand_label_method_processing_diff = 'diff'  # Разница значений
mesurand_label_method_processing_sum = 'sum'    # Просуммированное за определенное время значение
mesurand_label_method_processing_set = 'set'    # Множество уникальных значений
mesurand_label_method_processing_count = 'count'    # Количество значений
mesurand_label_method_processing_vec_avg = 'vect_avg'     # Среднее вектороное значение
mesurand_label_method_processing_median = 'median'  # Медианное значение

"""Table exist"""
table_exist = []
"""SQL"""
"Table"
scheme_data = 'meteo_point'
scheme_info = 'info'
table_in_data_1_minute = 'sensor'
table_in_data_1_hour = 'sensor_stat_minute'
table_in_data_1_day = 'sensor_stat_hour'
table_in_data_1_month = 'sensor_stat_day'
table_in_data_1_year = 'sensor_stat_month'
table_out_data_year = 'sensor_stat_year'
table_out_data_1 = 'sensor_stat'
table_section_minute_out_data = 'minute'
table_section_hour_out_data = 'hour'
table_section_day_out_data = 'day'
table_section_month_out_data = 'month'
table_section_year_out_data = 'year'
table_measurand = 'measurand'
table_measurand_processing = 'measurand_processing'
table_measurand_processing_statistic = 'measurand_processing_interval'

"""Permission"""
permission = f"ALTER TABLE {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" OWNER TO meteocube_master; " \
             f"GRANT ALL ON TABLE  {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" TO postgres; " \
             f"GRANT ALL ON TABLE  {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" TO meteocube_master; " \
             f"REVOKE ALL ON TABLE  {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" FROM meteocube_level1; " \
             f"GRANT SELECT, INSERT, UPDATE ON TABLE  {scheme_data}." \
             f"table_section_out_data_table_date_sections"\
             f" TO meteocube_level1;" \
             f" REVOKE ALL ON TABLE  {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" FROM meteocube_level2; " \
             f"GRANT SELECT ON TABLE  {scheme_data}.table_section_out_data_" \
             f"table_date_sections" \
             f" TO meteocube_level2;"


table_request_sensor = f'{scheme_data}.{{table_in_data}}'

sql_id_condition = "{AND} {COLUMN} {NOT} in ({ID_COLUMN}) "

request_id_condition = "{LABEL} in ({LABEL_MEASURAND})"

request_data_sens = "date_trunc('{PERIOD}', time_obs) + (interval '{INTERVAL}') as time, " \
                    "source_id, measurand_id, " \
                    "case when measurand_id not in ({WIND}) and method_processing not in ({COUNT}) " \
                    "then min(value_float[1]) end, " \
                    "case when measurand_id not in ({WIND}) and method_processing not in ({COUNT}) " \
                    "then max(value_float[1]) end, " \
                    "case when measurand_id not in ({WIND}) and method_processing not in ({COUNT}) " \
                    "then round(avg(value_float[1])::numeric, {ZNK})::float end, " \
                    "case when method_processing not in ({COUNT}) and method_processing in ({MEDIAN}) " \
                    "then round(percentile_cont(0.5) within group " \
                    "(order by value_float[1])::numeric, {ZNK})::float end, " \
                    "json_agg(distinct value_text), " \
                    "case when method_processing not in ({COUNT}) " \
                    "then array_agg(value_float[1]) end, " \
                    "case when method_processing = {COUNT} then sum(value_float[1]) end, " \
                    "method_processing"

request_data_sens_minute = "date_trunc('{PERIOD}', time_obs) + (interval '{INTERVAL}') as time, " \
                           "source_id, measurand_id, " \
                           "case when measurand_id not in ({WIND}) then min(value_float[1]) end, " \
                           "case when measurand_id not in ({WIND}) then max(value_float[1]) end, " \
                           "case when measurand_id not in ({WIND}) then " \
                           "round(avg(value_float[1])::numeric, {ZNK})::float end, " \
                           "round(percentile_cont(0.5) within group " \
                           "(order by value_float[1])::numeric, {ZNK})::float , " \
                           "json_agg(distinct value_text), " \
                           "case when measurand_id in ({WIND}) then array_agg(value_float[1]) end, " \
                           "count(measurand_id)"


wind_request_parameter_minute = "source_id, measurand_id, array_agg(value_float[1]), " \
                     "round(percentile_cont(0.5) within group (order by value_float[1])::numeric, {znk})::float, " \
                     "json_agg(value_text), count(value_float)".format(znk=znk)

wind_request_parameter = "source_id, measurand_id, array_agg(value_float[1]), " \
                     "round(percentile_cont(0.5) within group (order by value_float[1])::numeric, {znk})::float, " \
                     "json_agg(value_text), " \
                         "case when method_processing = {x} then sum(value_float[1])".format(znk=znk,
                                                                                             x='{METHOD_PROCESSING}')

request_condition_sensors = "(time_obs >= '{TIME_BEGIN}' and time_obs < '{TIME_END}') {AND} {MEASURAND} " \
                        "and ((value_float is not null and value_float[1] is not null) or " \
                        "(value_text is not null and value_text[1] is not null))"

sql_group_sensors = "time, source_id, measurand_id{NO_MINUTE}"

request_group_having = "count(value_float) != 0 or count(value_text) != 0"

sql_value_pattern = "({SOURCE_ID}, {MEASURAND_ID}, {METHOD_PROCESSING}, {TIME_INTERVAL}, '{TIME_OBS}','{TIME_REC}'," \
                    "{VALUE_FLOAT}, {VALUE_TEXT})"

insert_parameter_values = "source_id, measurand_id, method_processing, time_interval, " \
                          "time_obs, time_rec, value_float, value_text"



