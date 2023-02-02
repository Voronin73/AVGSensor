import math
from datetime import datetime, timedelta
from settings import znk, measurand_labels_not_avg, sql_no_mesurand_pattern, \
    measurand_winds_label, sql_label_pattern, sql_condition_sensors,\
    DB_POLIGON_USER, DB_POLIGON_PASSWD, DB_POLIGON_HOST, DB_POLIGON_PORT, DB_POLIGON_NAME
from connection import ConnectionManager
from log_files import info
from constants import start_dir


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


def sql_request(time_finish='', period=1440, avg_time=1, col_string=3000, timeout=60):

    if period < avg_time:
        info(f'Не верно задан период "{period}" и время осреднения данных "{avg_time}".'
             f' Врямя осредения должно быть меньше периода.', start_dir)
        return None

    elif avg_time > 1440*2:
        info(f'Не верно задано время осреднения данных "{avg_time}".'
             f' Врямя осредения должно быть меньше 2880 минут (48 часов)ю', start_dir)
        return None

    tNow = datetime.utcnow()
    if not time_finish:
        tFinish = tNow - timedelta(minutes=avg_time) + (datetime.min - tNow) % timedelta(minutes=avg_time)
        tStart = tFinish - timedelta(minutes=period)

    else:
        tFinish = datetime.strptime(time_finish, '%Y-%m-%d %H:%M:%S')
        tStart = tFinish - timedelta(minutes=period)

    if tFinish - timedelta(minutes=avg_time) < tStart:
        info(f'Не верно задан период "{period}" и время осреднения данных "{avg_time}".'
             f' Врямя осредения должно быть меньше периода.', start_dir)
        return None

    tStart_func = tStart
    print(tStart, tFinish)
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

        while tStart < tFinish:
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
