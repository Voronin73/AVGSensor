from settings import *
from constants import start_dir
from log_files import info
from exel_files import add_exel_files
from connection import ConnectionManager
from functions import check_time, conditions, values_out, get_avg_direction, get_avg_direction_vector,\
    auto_period_avg, create_info
from datetime import datetime


def avg(
        time_start='', time_finish='', auto='', avg_time='1_minute', source=None, measurand=None,
        no_source=None, no_measurand=None, sql_table=None, exel=None,
        col_string=3000000, timeout=180
):
    tStart_func = datetime.utcnow()

    # Определяем какуда писать результат
    if exel == 1:
        values_exel = []
    else:
        values_exel = None
    if sql_table == 1:
        values = ''
    else:
        values = None

    db = ConnectionManager(
        ip=DB_POLIGON_HOST, port=DB_POLIGON_PORT, db_name=DB_POLIGON_NAME,
        user=DB_POLIGON_USER, password=DB_POLIGON_PASSWD, timeout=timeout
    )
    try:

        # Определяем id ветра
        measurand_condition = ''
        for x in measurand_winds_label:
            if measurand_condition:
                measurand_condition += f", '{x[0]}'"
                measurand_condition += f", '{x[1]}'"
            else:
                measurand_condition += f"'{x[0]}'"
                measurand_condition += f", '{x[1]}'"

        condition = ''
        if measurand_condition:
            condition = request_id_condition.format(LABEL='label', LABEL_MEASURAND=measurand_condition)
        db.requests(parameter='label, id', tabel=f'{scheme_info}.{table_measurand}', condition=condition)
        wind_measurand_id_list = {}
        wind_Measurand_id = ''
        if db.result:
            for x in db.result:
                wind_measurand_id_list[x[0]] = x[1]
                if wind_Measurand_id:
                    wind_Measurand_id += f', {x[1]}'
                else:
                    wind_Measurand_id += f'{x[1]}'
        else:
            db.disconnect()
            return

        # Определяем id межрандов не входящих в обработку

        no_measurand_condition = ''
        for x in measurand_labels_not_avg:
            if no_measurand_condition:
                no_measurand_condition += f", '{x}'"
            else:
                no_measurand_condition += f"'{x}'"

        condition = ''
        if no_measurand_condition:
            condition = request_id_condition.format(LABEL='label', LABEL_MEASURAND=no_measurand_condition)

        db.requests(parameter='id', tabel=f'{scheme_info}.{table_measurand}', condition=condition)
        no_measurand_id = ''
        no_source_id = ''
        measurand_id = ''
        source_id = ''

        if db.result:
        # Формирования списка запрещенных межрандов
            for x in db.result[0]:
                if x:
                    if no_measurand_id:
                        no_measurand_id += f', {x}'
                    else:
                        no_measurand_id += f'{x}'
        if no_measurand:
            for x in no_measurand:
                if x:
                    if no_measurand_id:
                        no_measurand_id += f', {x}'
                    else:
                        no_measurand_id += f'{x}'

        # Формирование списка разрещенных межрандов
        if measurand:
            for x in measurand:
                if x:
                    if measurand_id:
                        measurand_id += f', {x}'
                    else:
                        measurand_id += f'{x}'

        # Формирование списка запрещеных источников
        if no_source:
            for x in no_source:
                if x:
                    if no_source_id:
                        no_source_id += f', {x}'
                    else:
                        no_source_id += f'{x}'

        # Формироване списка разрешенных источников
        if source:
            for x in source:
                if x:
                    if source_id:
                        source_id += f', {x}'
                    else:
                        source_id += f'{x}'

        # Определяем id metoth_processing
        db.requests(parameter='method_processing, id', tabel=f'{scheme_info}.{table_measurand_processing}')
        method_processing = {}
        if db.result:
            for x in db.result:
                method_processing[x[0]] = x[1]
        else:
            db.disconnect()
            return

        ############################################################################
        times = check_time(time_start=time_start, time_finish=time_finish, avg_time=avg_time)
        if not times:
            db.disconnect()
            return

        tSTART, tFINISH = times

        period_avg_time = auto_period_avg(tSTART, tFINISH, avg_time, auto)

        for avg_time in period_avg_time:

            times = create_info(
                time_start=tSTART, time_finish=tFINISH, avg_time=avg_time,
                wind_id=wind_Measurand_id, count_id=method_processing[mesurand_label_method_processing_count],
                median_id=method_processing[mesurand_label_method_processing_median]
            )
            if not times:
                db.disconnect()
                return

            # Определяем ID time_interval для для записи в таблицу

            period_times, time_avg, table_in_date, table_out_data, formate, \
                request_parameter, request_group, tStart, tFinish = times

            condition = request_id_condition.format(LABEL='time_interval', LABEL_MEASURAND=f"'{time_avg}'")
            db.requests(parameter='id', tabel=f'{scheme_info}.{table_measurand_processing_statistic}',
                        condition=condition)

            if db.result:
                time_interval_id = db.result[0][0]
            else:
                db.disconnect()
                return


            for times in period_times:
                n = 0
                while True:
                    tStart, tFinish, table_section_date, section_start_condition, section_end_condition = times

                    # Формирование запроса для получения данных
                    time_start = tStart.strftime(formate)
                    time_finish = tFinish.strftime(formate)

                    condition = conditions(source_id=source_id, measurand_id=measurand_id, no_source_id=no_source_id,
                                           no_measurand_id=no_measurand_id)
                    # Формируем условие запроса
                    if condition:
                        condition = request_condition_sensors.format(
                            TIME_BEGIN=time_start, TIME_END=time_finish, AND="and", MEASURAND=condition
                        )
                    else:
                        condition = request_condition_sensors.format(
                            TIME_BEGIN=time_start, TIME_END=time_finish, AND="", MEASURAND=""
                        )
                    db.requests(parameter=request_parameter, tabel=f'{scheme_data}.{table_in_date}', condition=condition,
                                group=request_group, group_having=request_group_having, x=col_string)

                    wind_data = {}
                    if db.result:

                        for x in db.result:

                            time_obs = x[0].strftime(formate)
                            k = 0
                            if len(x) == 11:
                                k = x[10]
                            # Количество данных используемое в обработке пишем в запрос
                            if x[9]:
                                if avg_time == '1_minute' or \
                                        k == method_processing[mesurand_label_method_processing_count]:
                                    values, values_exel = values_out(
                                        values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                        method_processing=method_processing[mesurand_label_method_processing_count],
                                        time_interval=time_interval_id, time_obs=time_obs, value_data=x[9])

                            if x[6]:
                                values, values_exel = values_out(
                                    values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                    method_processing=method_processing[mesurand_label_method_processing_median],
                                    time_interval=time_interval_id, time_obs=time_obs, value_data=x[6])

                            if x[2] in wind_measurand_id_list.values():
                                # Если ветер то пишем его в словарь для дальнейшей обработки
                                for z in [
                                    method_processing[mesurand_label_method_processing_avg],
                                    method_processing[mesurand_label_method_processing_vec_avg],
                                    method_processing[mesurand_label_method_processing_min],
                                    method_processing[mesurand_label_method_processing_max]
                                ]:
                                    if avg_time == '1_minute':

                                        if wind_data:
                                            if time_obs in wind_data.keys():
                                                if x[1] in wind_data[time_obs].keys():
                                                    if x[2] in wind_data[time_obs][x[1]].keys():
                                                        wind_data[time_obs][x[1]][x[2]][z] = x[8]
                                                    else:
                                                        wind_data[time_obs][x[1]][x[2]] = {z: x[8]}
                                                else:
                                                    wind_data[time_obs][x[1]] = {x[2]: {z: x[8]}}

                                            else:
                                                wind_data[time_obs] = {x[1]: {x[2]: {z: x[8]}}}
                                        else:
                                            wind_data = {time_obs: {x[1]: {x[2]: {z: x[8]}}}}
                                    else:
                                        if z == k:
                                            if wind_data:
                                                if time_obs in wind_data.keys():
                                                    if x[1] in wind_data[time_obs].keys():
                                                        if x[2] in wind_data[time_obs][x[1]].keys():
                                                            wind_data[time_obs][x[1]][x[2]][x[10]] = x[8]
                                                        else:
                                                            wind_data[time_obs][x[1]][x[2]] = {x[10]: x[8]}
                                                    else:
                                                        wind_data[time_obs][x[1]] = {x[2]: {x[10]: x[8]}}

                                                else:
                                                    wind_data[time_obs] = {x[1]: {x[2]: {x[10]: x[8]}}}
                                            else:
                                                wind_data = {time_obs: {x[1]: {x[2]: {x[10]: x[8]}}}}

                            if x[7][0]:
                                # Если текст то обрабатываем и пишем в запрос
                                val = ''
                                for y in x[7]:
                                    for z in y:
                                        if z not in val:
                                            if val:
                                                val += f', {z}'
                                            else:
                                                val = z

                                values, values_exel = values_out(
                                    values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                    method_processing=method_processing[mesurand_label_method_processing_set],
                                    time_interval=time_interval_id, time_obs=time_obs, value_data=val)
                            if x[3]:
                                if avg_time == '1_minute' or \
                                        k == method_processing[mesurand_label_method_processing_min]:
                                    values, values_exel = values_out(
                                        values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                        method_processing=method_processing[mesurand_label_method_processing_min],
                                        time_interval=time_interval_id, time_obs=time_obs, value_data=x[3])
                            if x[4]:
                                if avg_time == '1_minute' or \
                                        k == method_processing[mesurand_label_method_processing_max]:
                                    values, values_exel = values_out(
                                        values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                        method_processing=method_processing[mesurand_label_method_processing_max],
                                        time_interval=time_interval_id, time_obs=time_obs, value_data=x[4])
                            if x[5]:
                                if avg_time == '1_minute' or \
                                        k == method_processing[mesurand_label_method_processing_avg]:
                                    values, values_exel = values_out(
                                        values=values, values_exel=values_exel, source_id=x[1], measurand_id=x[2],
                                        method_processing=method_processing[mesurand_label_method_processing_avg],
                                        time_interval=time_interval_id, time_obs=time_obs, value_data=x[5])

                        db.result = None
                        break
                    elif db.result_err == 'connection timeout':
                        n += 1
                        if n > 11:
                            db.disconnect()
                            return tStart_func, tFINISH, period_avg_time, datetime.utcnow() - tStart_func, db.result_err
                    else:
                        info(f'Отсутствуют данные за период "{time_start} - {time_finish}."', start_dir)
                        break

                    db.result = None
                    # Обработка данных ветра
                    for x in wind_data.keys():
                        for k in wind_data[x].keys():
                            for z in measurand_winds_label:
                                if wind_measurand_id_list[z[0]] in wind_data[x][k].keys() and \
                                       wind_measurand_id_list[z[1]] in wind_data[x][k].keys():
                                    if method_processing[mesurand_label_method_processing_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(
                                            sum(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                [method_processing[mesurand_label_method_processing_avg]]) /
                                            len(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                [method_processing[mesurand_label_method_processing_avg]]), znk
                                        )

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                    if method_processing[mesurand_label_method_processing_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[1]]].keys():

                                        wind_direction = get_avg_direction(
                                            wind_data[x][k][wind_measurand_id_list[z[1]]]
                                            [method_processing[mesurand_label_method_processing_avg]]
                                        )

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[1]],
                                            method_processing=method_processing[mesurand_label_method_processing_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_direction)

                                    if method_processing[mesurand_label_method_processing_vec_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys() and \
                                            method_processing[mesurand_label_method_processing_vec_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[1]]].keys():

                                        wind_speed, wind_direction = get_avg_direction_vector(
                                            wind_data[x][k][wind_measurand_id_list[z[0]]]
                                            [method_processing[mesurand_label_method_processing_vec_avg]],
                                            wind_data[x][k][wind_measurand_id_list[z[1]]]
                                            [method_processing[mesurand_label_method_processing_vec_avg]]
                                        )

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_vec_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[1]],
                                            method_processing=method_processing[mesurand_label_method_processing_vec_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_direction)

                                    if method_processing[mesurand_label_method_processing_max] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(max(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                               [method_processing[mesurand_label_method_processing_max]]),
                                                           znk)

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_max],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                    if method_processing[mesurand_label_method_processing_min] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(min(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                               [method_processing[mesurand_label_method_processing_min]]),
                                                           znk)

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_min],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                elif wind_measurand_id_list[z[0]] in wind_data[x][k].keys():

                                    if method_processing[mesurand_label_method_processing_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(
                                            sum(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                [method_processing[mesurand_label_method_processing_avg]]) /
                                            len(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                [method_processing[mesurand_label_method_processing_avg]]), znk
                                        )
                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                    if method_processing[mesurand_label_method_processing_max] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(max(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                               [method_processing[mesurand_label_method_processing_max]]),
                                                           znk)

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_max],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                    if method_processing[mesurand_label_method_processing_min] in \
                                            wind_data[x][k][wind_measurand_id_list[z[0]]].keys():

                                        wind_speed = round(min(wind_data[x][k][wind_measurand_id_list[z[0]]]
                                                               [method_processing[mesurand_label_method_processing_min]]),
                                                           znk)

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[0]],
                                            method_processing=method_processing[mesurand_label_method_processing_min],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_speed)

                                elif wind_measurand_id_list[z[1]] in wind_data[x][k].keys():

                                    if method_processing[mesurand_label_method_processing_avg] in \
                                            wind_data[x][k][wind_measurand_id_list[z[1]]].keys():

                                        wind_direction = get_avg_direction(
                                            wind_data[x][k][wind_measurand_id_list[z[1]]]
                                            [method_processing[mesurand_label_method_processing_avg]]
                                        )

                                        values, values_exel = values_out(
                                            values=values, values_exel=values_exel, source_id=k,
                                            measurand_id=wind_measurand_id_list[z[1]],
                                            method_processing=method_processing[mesurand_label_method_processing_avg],
                                            time_interval=time_interval_id, time_obs=x, value_data=wind_direction)

                if values:
                    if f'{scheme_data}.{table_out_data}_{table_section_date}' not in table_exist:

                        db.create_tables_partition(scheme_data, [table_out_data, table_section_date],
                                                   condition=f"('{section_start_condition}') to "
                                                             f"('{section_end_condition} ')",
                                                   comment=f'Данные за ... дату {section_start_condition}.')

                        if db.result != 'error':
                            if len(table_exist) >= 10:
                                table_exist.pop(9)
                            table_exist.append(db.result)

                    db.inserts(scheme_data, [table_out_data, table_section_date],
                               insert_parameter_values, values, description=f'{time_start} - {time_finish}')
                    values = ''
                # if values_exel:
                #     add_exel_files(values_exel, avg_time, time_start=tStart_func, time_finish=tFinish)
                #


        db.disconnect()
        return tSTART, tFINISH, period_avg_time, datetime.utcnow() - tStart_func, None
    except KeyboardInterrupt:
        db.disconnect()
