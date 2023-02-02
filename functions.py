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

    namespace = parser.parse_args(argv[1:])

    return namespace.prev_day, namespace.start_time, namespace.finish_time, namespace.period,\
        namespace.avg_time, namespace.col_string, namespace.timeout


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
    return avg_direction, avg_speed


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
    return avg_direction, avg_speed


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


def sql_request(time_start='', time_finish='', period=1440, avg_time=1, col_string=3000, timeout=60, prev_days=0):

    tNow = datetime.utcnow()
    times = check_time(
        time_start=time_start, time_finish=time_finish, period=period, avg_time=avg_time, prev_days=prev_days
    )
    if not times:
        return
    tStart_func, tStart, tFinish = times

    poligon_db = ConnectionManager(
        ip=DB_POLIGON_HOST, port=DB_POLIGON_PORT, db_name=DB_POLIGON_NAME,
        user=DB_POLIGON_USER, password=DB_POLIGON_PASSWD, timeout=timeout
    )

    try:
        condition_measurand_wind = ''
        for label in measurand_winds_label:
            if label:
                if condition_measurand_wind:
                    condition_measurand_wind += ' or ' + sql_label_measurands.format(LABEL_MEASURAND=label[0], NOT='')
                    condition_measurand_wind += ' or ' + sql_label_measurands.format(LABEL_MEASURAND=label[1], NOT='')
                else:
                    condition_measurand_wind += '(' + sql_label_measurands.format(LABEL_MEASURAND=label[0], NOT='')
                    condition_measurand_wind += ' or ' + sql_label_measurands.format(LABEL_MEASURAND=label[1], NOT='')
        condition_measurand_wind += ') and'

        condition_no_measurand = ''
        for label in measurand_winds_label:
            if label:
                measurand_labels_not_avg.append(label[0])
                measurand_labels_not_avg.append(label[1])
        for label in measurand_labels_not_avg:
            if label:
                if condition_no_measurand:
                    condition_no_measurand += ' and ' + sql_label_measurands.format(LABEL_MEASURAND=label, NOT='NOT')
                else:
                    condition_no_measurand = sql_label_measurands.format(LABEL_MEASURAND=label, NOT='NOT')
        condition_no_measurand += ' and'

        while tStart <= tFinish - timedelta(minutes=avg_time):
            time_beginning = tStart.strftime('%Y-%m-%d %H:%M:%S')
            time_end = (tStart + timedelta(minutes=avg_time)).strftime('%Y-%m-%d %H:%M:%S')
            table_section = (tStart + timedelta(minutes=avg_time)).strftime('%Y_%m_%d')
            print(table_section)        # НЕ ЗАБЫТЬ ЗАКОМЕНТИРОВАТЬ!!!!!!!!!
            poligon_db.requests(
                parameter=sql_parameter_no_wind, tabel=table_request_sensor,
                condition=sql_condition_sensors.format(TIME_BEGIN=time_beginning,
                                                       TIME_END=time_end, MEASURAND=condition_no_measurand),
                x=col_string
            )
            # print(len(poligon_db.result))
            sens = {}
            values = ''
            if poligon_db.result:
                # Формирование словаря по ключам source_id с словарями по ключам measurand_id
                for x in poligon_db.result:
                    # print(x)
                    if x[0] in sens:
                        sens[x[0]][x[1]] = [x[2], x[3], x[4]]
                    else:
                        sens[x[0]] = {x[1]: [x[2], x[3], x[4]]}

            poligon_db.requests(
                parameter=sql_parameter_wind, tabel=table_request_sensor,
                condition=sql_condition_sensors.format(TIME_BEGIN=time_beginning,
                                                       TIME_END=time_end,
                                                       MEASURAND=condition_measurand_wind),
                x=col_string
            )
            # print(poligon_db.result)
            if poligon_db.result:
                sens_wind = {}
                for x in poligon_db.result:
                    if x[0] in sens_wind:
                        sens_wind[x[0]][x[1]] = x[2]
                    else:
                        sens_wind[x[0]] = {x[1]: x[2]}
                # print(sens_wind)
            #
                for sensor_id in sens_wind.keys():
                    for wind in measurand_winds_label:    # Если ветер то обрабатываем его
                        if wind[0] in list(sens_wind[sensor_id].keys()) and\
                                wind[1] in list(sens_wind[sensor_id].keys()):
                            avg_wind = get_avg_direction(sens_wind[sensor_id][wind[0]], sens_wind[sensor_id][wind[1]])
                            avg_wind_vector = get_avg_direction_vector(
                                sens_wind[sensor_id][wind[0]], sens_wind[sensor_id][wind[1]]
                            )

                            max_value = round(max(sens_wind[sensor_id][wind[0]]), znk)
                            min_value = round(min(sens_wind[sensor_id][wind[0]]), znk)
                            print(time_end, sensor_id, avg_wind, avg_wind_vector, max_value, min_value)

                            # del sens[sensor_id][wind[0]]
                            # del sens[sensor_id][wind[1]]

                        elif wind[0] in list(sens_wind[sensor_id].keys()):
                            avg_value = round(
                                sum(sens_wind[sensor_id][wind[0]])/len(sens_wind[sensor_id][wind[0]]), znk
                            )
                            max_value = round(max(sens_wind[sensor_id][wind[0]]), znk)
                            min_value = round(min(sens_wind[sensor_id][wind[0]]), znk)
                            print(time_end, sensor_id, avg_value, max_value, min_value)

                            # del sens[sensor_id][wind[0]]

                        elif wind[1] in list(sens_wind[sensor_id].keys()):
                            avg_value = round(get_avg_direction(sens_wind[sensor_id][wind[0]], 1)[0], znk)
                            print(time_end, sensor_id, avg_value)

                            # del sens[sensor_id][wind[1]]
            #
            #         if sens[sensor_id]:
            #             for mesurand in sens[sensor_id].keys():
            #                 avg_value = round(sum(sens[sensor_id][mesurand])/len(sens[sensor_id][mesurand]), znk)
            #                 max_value = round(max(sens[sensor_id][mesurand]), znk)
            #                 min_value = round(min(sens[sensor_id][mesurand]), znk)
            #                 print(time_end, sensor_id, mesurand, avg_value, max_value, min_value)

            tStart = tStart + timedelta(minutes=avg_time)

        poligon_db.disconnect()
        return tStart_func, tFinish, avg_time, datetime.utcnow() - tNow
    except KeyboardInterrupt:
        poligon_db.disconnect()
