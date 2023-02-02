import math
from datetime import datetime, timedelta
from settings import znk, measurand_labels_not_avg, sql_no_mesurand_pattern, \
    measurand_winds_label, sql_label_pattern, sql_condition_sensors,\
    DB_POLIGON_USER, DB_POLIGON_PASSWD, DB_POLIGON_HOST, DB_POLIGON_PORT, DB_POLIGON_NAME
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
        condition = ''
        for label in measurand_labels_not_avg:
            if condition:
                condition = ' and ' + sql_label_pattern.format(LABEL_MEASURAND=label)
            else:
                condition = sql_label_pattern.format(LABEL_MEASURAND=label)

        poligon_db.requests('id', 'info.measurand', condition)

        sql_no_mesurand = ''
        if poligon_db.result:
            for mesurand_ids in poligon_db.result:
                for mesurand_id in mesurand_ids:
                    sql_no_mesurand = sql_no_mesurand_pattern.format(NOT_MEASURAND=mesurand_id)
        else:
            sql_no_mesurand = ' and '

        measurand_winds = []
        n = 0
        for measurand_list in measurand_winds_label:
            if measurand_list:
                measurand_winds.append([])
                for measurand in measurand_list:
                    poligon_db.requests(parameter='id', tabel='info.measurand', condition=f"label like '{measurand}'")
                    measurand_winds[n].append(str(poligon_db.result[0][0]))
            n += 1

        while tStart <= tFinish - timedelta(minutes=avg_time):
            time_beginning = tStart.strftime('%Y-%m-%d %H:%M:%S')
            time_end = (tStart + timedelta(minutes=avg_time)).strftime('%Y-%m-%d %H:%M:%S')
            table_section = (tStart + timedelta(minutes=avg_time)).strftime('%Y_%m_%d')
            print(table_section)        # НЕ ЗАБЫТЬ ЗАКОМЕНТИРОВАТЬ!!!!!!!!!
            poligon_db.requests(
                parameter='source_id, measurand_id, value_float', tabel='meteo_point.sensor',
                condition=sql_condition_sensors.format(TIME_BEGIN=time_beginning,
                                                       TIME_END=time_end, NOT_MEASURAND=sql_no_mesurand
                                                       ), x=col_string
            )
            # print(len(poligon_db.result))
            if poligon_db.result:
                sens = {}
                # Формирование словаря по ключам source_id с словарями по ключам measurand_id
                for x in poligon_db.result:
                    if str(x[0]) in sens:
                        if str(x[1]) in sens[str(x[0])]:
                            for y in x[2]:
                                sens[str(x[0])][str(x[1])].append(y)
                        else:
                            sens[str(x[0])][str(x[1])] = x[2]
                    else:
                        sens[str(x[0])] = {str(x[1]): x[2]}
                # print(len(sens))

                for sensor_id in sens.keys():
                    for wind in measurand_winds:    # Если ветер то обрабатываем его
                        if wind[0] in list(sens[sensor_id].keys()) and wind[1] in list(sens[sensor_id].keys()):
                            avg_wind = get_avg_direction(sens[sensor_id][wind[0]], sens[sensor_id][wind[1]])
                            avg_wind_vector = get_avg_direction_vector(
                                sens[sensor_id][wind[0]], sens[sensor_id][wind[1]]
                            )

                            max_value = round(max(sens[sensor_id][wind[0]]), znk)
                            min_value = round(min(sens[sensor_id][wind[0]]), znk)
                            print(time_end, sensor_id, avg_wind, avg_wind_vector, max_value, min_value)

                            del sens[sensor_id][wind[0]]
                            del sens[sensor_id][wind[1]]

                        elif wind[0] in list(sens[sensor_id].keys()):
                            avg_value = round(sum(sens[sensor_id][wind[0]])/len(sens[sensor_id][wind[0]]), znk)
                            max_value = round(max(sens[sensor_id][wind[0]]), znk)
                            min_value = round(min(sens[sensor_id][wind[0]]), znk)
                            print(time_end, sensor_id, avg_value, max_value, min_value)

                            del sens[sensor_id][wind[0]]

                        elif wind[1] in list(sens[sensor_id].keys()):
                            avg_value = round(get_avg_direction(sens[sensor_id][wind[0]], 1)[0], znk)
                            print(time_end, sensor_id, avg_value)

                            del sens[sensor_id][wind[1]]

                    if sens[sensor_id]:
                        for mesurand in sens[sensor_id].keys():
                            avg_value = round(sum(sens[sensor_id][mesurand])/len(sens[sensor_id][mesurand]), znk)
                            max_value = round(max(sens[sensor_id][mesurand]), znk)
                            min_value = round(min(sens[sensor_id][mesurand]), znk)
                            print(time_end, sensor_id, mesurand, avg_value, max_value, min_value)

            tStart = tStart + timedelta(minutes=avg_time)

        poligon_db.disconnect()
        return tStart_func, tFinish, avg_time, datetime.utcnow() - tNow
    except KeyboardInterrupt:
        poligon_db.disconnect()
