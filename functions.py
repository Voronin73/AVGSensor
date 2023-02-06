import math
from datetime import datetime, timedelta
from settings import *
from connection import ConnectionManager
from log_files import info
from constants import start_dir
from argparse import ArgumentParser
from sys import argv


def arguments():
    parser = ArgumentParser(
        prog='AVGsensor',
        description='''Программа осреднения параметров метеорологических 
        датчиков за определенный период с указанным временным осреденнием.''',
        epilog='''OOO "ИРАМ" 2023. Автор программы, как всегда,
    не несет никакой ответственности ни за что.''',
        add_help=False
    )

    parser_group = parser.add_argument_group(title='Парамерты')
    parser_group.add_argument('--help', '-h', action='help', help='Справка')
    parser_group.add_argument(
        '-d', '--prev_day', type=int, default=0,
        help='Выполняется осреднение за количество предыдущих суток, '
             'указаное в переменной, с 00:00 по 00:00, не используются критерии периода осреднения. '
             'Если аргумент равен "0", выполняется осреднение по другим указаным критериям.'
             'По умолчанию занчение "0".',
        metavar=': количество суток'
    )
    parser_group.add_argument(
        '-s', '--start_time', type=str, default='',
        help='Время начала осреднения данных в формате "YY-MM-DD HH:mm". '
             'Не обязательный параметер.',
        metavar=': дата и время начала осреднения'
    )

    parser_group.add_argument(
        '-f', '--finish_time', type=str, default='',
        help='Время окончания осреднения данных в формате "YY-MM-DD HH:mm". '
             'Если параметер не введен используется текущее время.',
        metavar=': дата и время окончания осреднения'
    )
    parser_group.add_argument(
        '-p', '--period', type=int, default=1440,
        help='Используется если отсутствует параметер "Время начала остреднения". '
             'Период осреднения данных (время окончания осреднения данных - период осреднения данных = '
             'время начала осреднения данных), в минутах (по умолчанию 1440 минут (сутки)).',
        metavar=': период осреднения'
    )
    parser_group.add_argument(
        '-a', '--avg_time', type=int, default=1,
        help='Время осреднения данных в минутах (по умолчанию 1 минута).',
        metavar=': время осреднения'
    )
    parser_group.add_argument(
        '-c', '--col_string', type=int, default=30000,
        help='Максимальное количество строк получаемых от базы данных '
        '(чем больще период тем больше строк, по умолчанию 30000)',
        metavar=': количество получаемых строк'
    )
    parser_group.add_argument(
        '-t', '--timeout', type=int, default=60,
        help='Таймаут подключения и получения данных от базы данных в секундах (по умолчанию 60 секунд).',
        metavar=': таймаут'
    )

    parser_group.add_argument(
        '-id_s', '--source_id', type=int, default=[''], nargs='+',
        help='Список "id" источников информации.',
        metavar=': "id" источник информации'
    )

    parser_group.add_argument(
        '-no_id_s', '--no_source_id', type=int, default=[''], nargs='+',
        help='Список "id" не используемых источников информации.',
        metavar=': "id" не используемых источник информации'
    )

    parser_group.add_argument(
        '-id_m', '--measurand_id', type=int, default=[''], nargs='+',
        help='Список "id" параметров информации.',
        metavar=': "id" параметров информации.'
    )

    parser_group.add_argument(
        '-no_id_m', '--no_measurand_id', type=int, default=[''], nargs='+',
        help='Список "id" не используемых параметров информации.',
        metavar=': "id" не используемых параметров информации.'
    )

    parser_group.add_argument(
        '-l_m', '--measurand_label', type=str, default=[''], nargs='+',
        help='Список "label" параметров информации.',
        metavar=': "label" параметров информации.'
    )

    parser_group.add_argument(
        '-no_l_m', '--no_measurand_label', type=str, default=[''], nargs='+',
        help='Список "label" не используемых параметров информации.',
        metavar=': "label" не используемых параметров информации.'
    )

    namespace = parser.parse_args(argv[1:])

    return namespace.prev_day, namespace.start_time, namespace.finish_time, namespace.period,\
        namespace.avg_time, namespace.col_string, namespace.timeout, namespace.source_id,\
        namespace.no_source_id, namespace.measurand_id, namespace.no_measurand_id, \
        namespace.measurand_label, namespace.no_measurand_label


def get_avg_direction(speeds, directions):  # Осреднение без учета направления
    sinSum = 0
    cosSum = 0
    speed = 0
    for value1, value2 in zip(directions, speeds):
        sinSum += math.sin(math.radians(value1))
        cosSum += math.cos(math.radians(value1))
        speed += value2
    avg_direction = round((math.degrees(math.atan2(sinSum, cosSum)) + 360) % 360, znk)
    avg_speed = round(speed/len(speeds), znk)
    return avg_speed, avg_direction


def get_avg_direction_vector(speeds, directions):   # Осреднение с учетом скорости
    sinSum = 0.0
    cosSum = 0.0
    for value, speed in zip(directions, speeds):
        sinSum += speed * math.sin(math.radians(value))
        cosSum += speed * math.cos(math.radians(value))
    sinSum = sinSum / len(directions)
    cosSum = cosSum / len(directions)
    avg_direction = round((math.degrees(math.atan2(sinSum, cosSum)) + 360) % 360, znk)
    avg_speed = round(math.sqrt(cosSum**2 + sinSum**2), znk)
    return avg_speed, avg_direction


def time_format(date_time, formate='%y-%m-%d %H:%M:%S'):
    try:
        datetime.strptime(date_time, formate)
        return 'ok'
    except ValueError:
        return 'error'


def check_time(prev_days: int, time_start: str, time_finish: str, period: int, avg_time: int):

    tNow = datetime.utcnow()
    if prev_days == 0:
        formate = '%y-%m-%d %H:%M'

        if time_start:
            if time_format(time_start, formate) == 'ok':
                tStart = datetime.strptime(time_start, formate)
            else:
                info(f'Не верный формат времени начала "{time_start}".', start_dir)
                return None
            if time_finish:
                if time_format(time_start, formate) == 'ok':
                    tFinish = datetime.strptime(time_finish, formate)
                else:
                    info(f'Не верный формат времени окончания "{time_finish}".', start_dir)
                    return None

                if tFinish - timedelta(minutes=avg_time) < tStart:
                    info(f'Не верно заданo время начала "{time_start}" или время окончания "{time_finish}" '
                         f'или время осреднения данных "{avg_time}".', start_dir)
                    return None
            else:
                tFinish = tNow.replace(second=0, microsecond=0)
        else:
            if period < avg_time:
                info(f'Не верно задан период "{period}" и время осреднения данных "{avg_time}".'
                     f' Врямя осредения должно быть меньше периода.', start_dir)
                return None

            elif avg_time > 1440 * 2:
                info(f'Не верно задано время осреднения данных "{avg_time}".'
                     f' Врямя осредения должно быть меньше 2880 минут (48 часов)ю', start_dir)
                return None

            # tNow = datetime.utcnow()
            if not time_finish:
                tFinish = tNow - timedelta(minutes=avg_time) + (datetime.min - tNow) % timedelta(minutes=avg_time)
                tStart = tFinish - timedelta(minutes=period)

            else:
                tFinish = datetime.strptime(time_finish, '%Y-%m-%d %H:%M')
                tStart = tFinish - timedelta(minutes=period)

    else:
        tFinish = tNow.replace(hour=0, minute=0, second=0, microsecond=0)
        tStart = tFinish - timedelta(days=prev_days)

    if tFinish - timedelta(minutes=avg_time) < tStart:
        info(f'Не верно задан период "{period} мин." или время осреднения данных "{avg_time} мин.".'
             f' Врямя осредения должно быть меньше периода осреднения данных.', start_dir)
        return None

    tStart_func = tStart
    # print(tStart, tFinish)
    return tStart_func, tStart, tFinish


def values_out(values, source_id, measurand_id, method_processing, time_obs, value_floats, value_count):
    for parameter, value in zip(method_processing, value_floats):
        if values:
            values += ', '
        time_rec = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        values += sql_value_pattern.format(
            SOURCE_ID=source_id, MEASURAND_ID=measurand_id,
            METHOD_PROCESSING=sql_select_id_method_processing.format(
                AND='', LABEL='label', NOT='', LABEL_MEASURAND=parameter
            ),
            TIME_OBS=time_obs, TIME_REC=time_rec, VALUE=value, COUNT=value_count
        )
    return values


def conditions(source_id: list,  measurand_id: list, no_source_id: list,
               no_measurand_id: list, measurand_label: list, no_measurand_label: list):
    condition = ''
    column = ''
    denial = ''

    z = 0
    for k in [source_id, measurand_id, no_source_id, no_measurand_id, measurand_label, no_measurand_label]:
        ids = ''
        if k[0]:
            if z <= 3:
                if z <= 1:
                    denial = ''
                    if z == 0:
                        column = 'source_id'
                    else:
                        column = 'measurand_id'
                elif z <= 3:
                    denial = 'NOT'
                    if z == 2:
                        column = 'source_id'
                    else:
                        column = 'measurand_id'

                for n in k:
                    if ids:
                        ids += f', {n}'
                    else:
                        ids = f'{n}'

                if condition:
                    condition += sql_id_condition.format(AND='AND', COLUMN=column, NOT=denial, ID_COLUMN=ids)
                else:
                    condition = sql_id_condition.format(AND='', COLUMN=column, NOT=denial, ID_COLUMN=ids)
            else:
                column = 'label'
                if z == 4:
                    denial = ''
                    label = ''
                    for n in k:
                        if label:
                            label += sql_label_measurands.format(AND='OR', LABEL=column, NOT=denial,
                                                                 LABEL_MEASURAND=n)
                        else:
                            label = '(' + sql_label_measurands.format(AND='', LABEL=column, NOT=denial,
                                                                      LABEL_MEASURAND=n)
                    if label:
                        if condition:
                            condition += f' and {label}) '
                        else:
                            condition = f'{label}) '
                else:
                    denial = 'NOT'
                    for n in k:
                        if condition:
                            condition += sql_label_measurands.format(AND='AND', LABEL=column, NOT=denial,
                                                                     LABEL_MEASURAND=n)
                        else:
                            condition = sql_label_measurands.format(AND='', LABEL=column, NOT=denial,
                                                                    LABEL_MEASURAND=n)
        z += 1
    return condition



def sql_request(
        time_start='', time_finish='', period=1440, avg_time=1, source_id=None, measurand_id=None, no_source_id=None,
        no_measurand_id=None, measurand_label=None, no_measurand_label=None,
        col_string=3000, timeout=60, prev_days=0
):

    tNow = datetime.utcnow()
    times = check_time(
        time_start=time_start, time_finish=time_finish, period=period, avg_time=avg_time, prev_days=prev_days
    )
    if not times:
        return
    tStart_func, tStart, tFinish = times

    for no_label in no_measurand_label:
        if no_label:
            if no_label not in measurand_labels_not_avg:
                measurand_labels_not_avg.append(no_label)

    measurand_label_wind = []
    if measurand_label[0]:
        measurand_label_wind = measurand_label.copy()
    measurand_labels_not_avg_wind = measurand_labels_not_avg.copy()
    for label_wind in measurand_winds_label:
        for label in label_wind:
            if label not in measurand_label:
                measurand_label_wind.append(label)
            if label not in measurand_labels_not_avg:
                measurand_labels_not_avg.append(label)

    condition_sensor_wind = conditions(source_id=source_id, measurand_id=measurand_id, no_source_id=no_source_id,
                                       no_measurand_id=no_measurand_id, measurand_label=measurand_label_wind,
                                       no_measurand_label=measurand_labels_not_avg_wind
                                       )
    condition_sensor = conditions(source_id=source_id, measurand_id=measurand_id, no_source_id=no_source_id,
                                  no_measurand_id=no_measurand_id, measurand_label=measurand_label,
                                  no_measurand_label=measurand_labels_not_avg
                                  )

    poligon_db = ConnectionManager(
        ip=DB_POLIGON_HOST, port=DB_POLIGON_PORT, db_name=DB_POLIGON_NAME,
        user=DB_POLIGON_USER, password=DB_POLIGON_PASSWD, timeout=timeout
    )
    try:
        while tStart <= tFinish - timedelta(minutes=avg_time):
            time_beginning = tStart.strftime('%Y-%m-%d %H:%M:%S')
            time_end = (tStart + timedelta(minutes=avg_time)).strftime('%Y-%m-%d %H:%M:%S')
            table_section = (tStart + timedelta(minutes=avg_time)).strftime('%Y_%m_%d')
            print(table_section)        # НЕ ЗАБЫТЬ ЗАКОМЕНТИРОВАТЬ!!!!!!!!!
            poligon_db.requests(
                parameter=sql_parameter_no_wind, tabel=table_request_sensor,
                condition=sql_condition_sensors.format(TIME_BEGIN=time_beginning,
                                                       TIME_END=time_end, AND='AND', MEASURAND=condition_sensor),
                group=sql_group_sensors, group_having=sql_having_sensor, x=col_string
            )
            # print(poligon_db.result)
            sens = {}
            values = ''
            if poligon_db.result:
                method_processing = [
                    mesurand_label_method_processing_min,
                    mesurand_label_method_processing_max,
                    mesurand_label_method_processing_avg
                ]

                for x in poligon_db.result:
                    values = values_out(
                        values=values, source_id=x[0], measurand_id=x[2], method_processing=method_processing,
                        time_obs=time_end, value_floats=[x[3], x[4], x[5]], value_count=x[6]
                    )
                    # Формирование словаря по ключам source_id с словарями по ключам label_measurand
                    if x[0] in sens:
                        sens[x[0]][x[1]] = [x[2], [x[3], x[4], x[5]], x[6]]
                    else:
                        sens[x[0]] = {x[1]: [x[2], [x[3], x[4], x[5]], x[6]]}

            # print(values)
            poligon_db.requests(
                parameter=sql_parameter_wind, tabel=table_request_sensor,
                condition=sql_condition_sensors.format(TIME_BEGIN=time_beginning,
                                                       TIME_END=time_end, AND='AND',
                                                       MEASURAND=condition_sensor_wind),
                group=sql_group_sensors, group_having=sql_having_sensor, x=col_string
            )
            # print(poligon_db.result)
            if poligon_db.result:
                sens_wind = {}
                for x in poligon_db.result:
                    if x[0] in sens_wind:
                        sens_wind[x[0]][x[1]] = [x[2], x[3], x[4]]
                    else:
                        sens_wind[x[0]] = {x[1]: [x[2], x[3], x[4]]}
                # print(sens_wind)
            #
                for sensor_id in sens_wind.keys():
                    for wind in measurand_winds_label:    # Если ветер то обрабатываем его

                        max_value = ''
                        min_value = ''
                        avg_wind_vector_speed = ''
                        avg_wind_vector_direction = ''
                        avg_wind_speed = ''
                        avg_wind_direction = ''
                        method_processing_speed = []
                        method_processing_direction = []

                        if set(wind).issubset(sens_wind[sensor_id].keys()):

                            method_processing_speed = [mesurand_label_method_processing_min,
                                                       mesurand_label_method_processing_max,
                                                       mesurand_label_method_processing_avg]
                            method_processing_direction = [mesurand_label_method_processing_avg]


                            avg_wind_speed, avg_wind_direction = get_avg_direction(
                                sens_wind[sensor_id][wind[0]][1], sens_wind[sensor_id][wind[1]][1]
                            )
                            avg_wind_vector_speed, avg_wind_vector_direction = get_avg_direction_vector(
                                sens_wind[sensor_id][wind[0]][1], sens_wind[sensor_id][wind[1]][1]
                            )

                            max_value = round(max(sens_wind[sensor_id][wind[0]][1]), znk)
                            min_value = round(min(sens_wind[sensor_id][wind[0]][1]), znk)
                            print(time_end, sensor_id, avg_wind_speed,  avg_wind_direction, avg_wind_vector_speed,
                                  avg_wind_vector_direction, max_value, min_value)

                            # del sens[sensor_id][wind[0]]
                            # del sens[sensor_id][wind[1]]

                        elif wind[0] in list(sens_wind[sensor_id].keys()):
                            method_processing_speed = [mesurand_label_method_processing_min,
                                                       mesurand_label_method_processing_max,
                                                       mesurand_label_method_processing_avg]

                            avg_wind_speed = round(
                                sum(sens_wind[sensor_id][wind[0]][1])/len(sens_wind[sensor_id][wind[0]][1]), znk
                            )
                            max_value = round(max(sens_wind[sensor_id][wind[0]][1]), znk)
                            min_value = round(min(sens_wind[sensor_id][wind[0]][1]), znk)
                            print(time_end, sensor_id, avg_wind_speed, max_value, min_value)

                            # del sens[sensor_id][wind[0]]

                        elif wind[1] in list(sens_wind[sensor_id].keys()):
                            method_processing_direction = [mesurand_label_method_processing_avg]
                            avg_wind_direction = round(get_avg_direction(sens_wind[sensor_id][wind[0]], 1)[0], znk)
                            print(time_end, sensor_id, avg_wind_direction)

                        if avg_wind_speed:
                            values = values_out(
                                values=values, source_id=sensor_id, measurand_id=sens_wind[sensor_id][wind[0]][0],
                                method_processing=method_processing_speed,
                                time_obs=time_end, value_floats=[
                                    min_value, max_value, avg_wind_speed, avg_wind_vector_speed
                                ], value_count=sens_wind[sensor_id][wind[0]][2]
                            )
                        if avg_wind_direction:
                            values = values_out(
                                values=values, source_id=sensor_id, measurand_id=sens_wind[sensor_id][wind[1]][0],
                                method_processing=method_processing_direction,
                                time_obs=time_end, value_floats=[avg_wind_direction, avg_wind_vector_direction],
                                value_count=sens_wind[sensor_id][wind[1]][2]
                            )
            tStart = tStart + timedelta(minutes=avg_time)
            print(values)
            print(sens)
        poligon_db.disconnect()
        return tStart_func, tFinish, avg_time, datetime.utcnow() - tNow
    except KeyboardInterrupt:
        poligon_db.disconnect()
