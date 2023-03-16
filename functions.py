import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from settings import *
from log_files import info
from constants import start_dir
from argparse import ArgumentParser
from sys import argv


def table_existing(table_section):
    if table_section not in table_exist:
        if len(table_exist) >= 10:
            table_exist.pop(10)
        table_exist.append(table_section)
        return False
    else:
        return True


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
        '-s', '--start_time', type=str, default='',
        help='Время начала осреднения данных в формате "YYYY-MM-DD HH:mm:ss". '
             'Не обязательный параметер.',
        metavar=': дата и время начала осреднения'
    )
    parser_group.add_argument(
        '-f', '--finish_time', type=str, default='',
        help='Время окончания осреднения данных в формате "YYYY-MM-DD HH:mm:ss". '
             'Если параметер не введен используется текущее время.',
        metavar=': дата и время окончания осреднения'
    )
    parser_group.add_argument(
        '-u', '--auto', type=str, default='yes',
        help='Автоматически осреднять за час, день, месяц, год при пересечении границы. '
             'По умолчанию "yes".',
        metavar=': автоматическое осреднение'
    )
    parser_group.add_argument(
        '-a', '--avg_time', type=str, default="1_minute",
        help='Время осреднения данных: "1_minute" - 1 минута; "1_hour" - 1 час; "1_day" - 1 день;'
             ' "1_month" - 1 месяц; "1_year" - 1 год, (по умолчанию 1 минута).',
        metavar=': время осреднения'
    )
    parser_group.add_argument(
        '-c', '--col_string', type=int, default=3000000,
        help='Максимальное количество строк получаемых от базы данных '
        '(чем больще период тем больше строк, по умолчанию 30000)',
        metavar=': количество получаемых строк'
    )
    parser_group.add_argument(
        '-t', '--timeout', type=int, default=300,
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
        '-q', '--sql_table', type=int, default=1,
        help='Запись данных в базу данных. 0 - не писать, 1 - записать в файл.',
        metavar=': запись данных в EXEL файл.'
    )

    parser_group.add_argument(
        '-e', '--exel', type=int, default=0,
        help='Запись данных в EXEL файл. 0 - не писать, 1 - записать в файл.',
        metavar=': запись данных в EXEL файл.'
    )

    namespace = parser.parse_args(argv[1:])

    return namespace.start_time, namespace.finish_time, namespace.auto, \
        namespace.avg_time, namespace.col_string, namespace.timeout, namespace.source_id,\
        namespace.no_source_id, namespace.measurand_id, namespace.no_measurand_id, \
        namespace.sql_table, namespace.exel


def get_avg_direction(directions):  # Осреднение без учета направления
    sinSum = 0
    cosSum = 0

    for value1 in directions:
        sinSum += math.sin(math.radians(value1))
        cosSum += math.cos(math.radians(value1))
    avg_direction = round((math.degrees(math.atan2(sinSum, cosSum)) + 360) % 360, znk)

    return avg_direction


def get_avg_direction_vector(speeds: list, directions: list):   # Осреднение с учетом скорости
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


def check_time(time_start, time_finish, avg_time):

    formate = '%Y-%m-%d %H:%M:%S'
    tNow = datetime.utcnow()
    time_avg = avg_time.replace('_', ' ')
    tStart = None
    tFinish = None

    if time_avg == '1 minute':
        avg_time_datetime = relativedelta(minutes=1)
        if not time_start:
            tFinish = tNow.replace(hour=0, minute=0, second=0, microsecond=0)
            tStart = tFinish - relativedelta(days=1)

    elif time_avg == '1 hour':
        avg_time_datetime = relativedelta(hours=1)
        if not time_start:
            tFinish = tNow.replace(hour=0, minute=0, second=0, microsecond=0)
            tStart = tFinish - relativedelta(days=1)

    elif time_avg == '1 day':
        avg_time_datetime = relativedelta(days=1)
        if not time_start:
            tFinish = tNow.replace(hour=0, minute=0, second=0, microsecond=0)
            tStart = tFinish - relativedelta(days=1)

    elif time_avg == '1 month':
        avg_time_datetime = relativedelta(months=1)
        if not time_start:
            tFinish = tNow.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            tStart = tFinish - relativedelta(months=1)

    elif time_avg == '1 year':
        avg_time_datetime = relativedelta(years=1)
        if not time_start:
            tFinish = tNow.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            tStart = tFinish - relativedelta(years=1)

    else:
        return None

    if time_start:
        if len(time_start) < 18:
            time_start += ':00'
        if time_format(time_start, formate) == 'ok':
            tStart = datetime.strptime(time_start, formate)
        else:
            info(f'Не верный формат времени начала "{time_start}".', start_dir)
            return None
        if time_finish:
            if len(time_finish) < 18:
                time_finish += ':00'
            if time_format(time_start, formate) == 'ok':
                tFinish = datetime.strptime(time_finish, formate)
            else:
                info(f'Не верный формат времени окончания "{time_finish}".', start_dir)
                return None
            if tFinish - avg_time_datetime < tStart:
                info(f'Не верно заданo время начала "{time_start}" или время окончания "{time_finish}" '
                     f'или время осреднения данных "{time_avg}".', start_dir)
                return None
        else:
            tFinish = tNow.replace(second=0, microsecond=0)
    return tStart, tFinish


def create_info(time_start, time_finish, avg_time: str, wind_id: str, count_id: str, median_id: int):

    formate = '%Y-%m-%d %H:%M:%S'
    tStart = time_start
    tFinish = time_finish

    time_avg = avg_time.replace('_', ' ')

    if time_avg == '1 minute':
        avg_time_datetime = relativedelta(minutes=1)
        request_period = relativedelta(days=1)
        table_in_data = table_in_data_1_minute
        table_out_data = table_in_data_1_hour
        format_section_name = '%Y_%m_%d'
        request_parameter = request_data_sens_minute.format(PERIOD='minute', INTERVAL=time_avg,
                                                            WIND=wind_id, COUNT=count_id, ZNK=znk)
        request_group = sql_group_sensors.format(NO_MINUTE='')

    elif time_avg == '1 hour':
        avg_time_datetime = relativedelta(hours=1)
        request_period = relativedelta(days=1)
        table_in_data = table_in_data_1_hour
        table_out_data = table_in_data_1_day
        format_section_name = '%Y_%m_%d'
        request_parameter = request_data_sens.format(PERIOD='hour', INTERVAL=time_avg,
                                                     WIND=wind_id, COUNT=count_id, MEDIAN=median_id, ZNK=znk)
        request_group = sql_group_sensors.format(NO_MINUTE=', method_processing')
        tFinish = tFinish.replace(minute=0, second=0, microsecond=0)
        tStart = tStart.replace(minute=0, second=0, microsecond=0)

    elif time_avg == '1 day':
        avg_time_datetime = relativedelta(days=1)
        request_period = relativedelta(days=1)
        table_in_data = table_in_data_1_day
        table_out_data = table_in_data_1_month
        format_section_name = '%Y_%m_%d'
        request_parameter = request_data_sens.format(PERIOD='day', INTERVAL=time_avg,
                                                     WIND=wind_id, COUNT=count_id, MEDIAN=median_id, ZNK=znk)
        request_group = sql_group_sensors.format(NO_MINUTE=', method_processing')
        tFinish = tFinish.replace(hour=0, minute=0, second=0, microsecond=0)
        tStart = tStart.replace(hour=0, minute=0, second=0, microsecond=0)

    elif time_avg == '1 month':
        avg_time_datetime = relativedelta(months=1)
        request_period = relativedelta(months=1)
        table_in_data = table_in_data_1_month
        table_out_data = table_in_data_1_year
        format_section_name = '%Y_%m_%d'
        request_parameter = request_data_sens.format(PERIOD='month', INTERVAL=time_avg,
                                                     WIND=wind_id, COUNT=count_id, MEDIAN=median_id, ZNK=znk)
        request_group = sql_group_sensors.format(NO_MINUTE=', method_processing')
        tFinish = tFinish.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tStart = tStart.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    elif time_avg == '1 year':
        avg_time_datetime = relativedelta(years=1)
        request_period = relativedelta(years=1)
        table_in_data = table_in_data_1_year
        table_out_data = table_out_data_year
        format_section_name = '%Y_%m_%d'
        request_parameter = request_data_sens.format(PERIOD='year', INTERVAL=time_avg,
                                                     WIND=wind_id, COUNT=count_id, MEDIAN=median_id, ZNK=znk)
        request_group = sql_group_sensors.format(NO_MINUTE=', method_processing')
        # if not time_start:
        tFinish = tFinish.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        tStart = tStart.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    else:
        return None


    period_times_tmp = []
    tmp = tStart
    while tmp < tFinish:

        tmp1 = tmp

        if not period_times_tmp:
            tmp = tmp + avg_time_datetime
            if time_avg == '1 minute' or time_avg == '1 hour' or time_avg == '1 day':
                tmp = tmp.replace(hour=0, minute=0, second=0, microsecond=0)
            elif time_avg == '1 month':
                tmp = tmp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif time_avg == '1 year':
                tmp = tmp.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                return
            tmp2 = tmp
            tmp = tmp - avg_time_datetime
        else:
            tmp2 = tmp + avg_time_datetime
        tmp = tmp + request_period
        if tmp >= tFinish:
            tmp = tFinish

        period_times_tmp.append([tmp1, tmp, tmp2.strftime(format_section_name),
                                tmp2.strftime(formate), (tmp2 + request_period).strftime(formate)])
    period_times = []
    for x in period_times_tmp:
        s = x[0]
        f = x[1]
        while s < f:
            s1 = s
            s = s + avg_time_datetime
            period_times.append([s1, s, x[2], x[3], x[4]])

    return period_times, time_avg, table_in_data, table_out_data, \
        formate, request_parameter, request_group, tStart, tFinish


def auto_period_avg(start, finish, avg_time, auto):
    period_avg_time = []
    if auto.lower() == 'yes':
        day_start = start.day
        month_start = start.month
        year_start = start.year
        day_finish = finish.day
        month_finish = finish.month
        year_finish = finish.year
        if day_start == day_finish and month_start == month_finish and year_start == year_finish:
            period_avg_time = ['1_minute']
        elif year_start != year_finish:
            if avg_time == '1_minute':
                period_avg_time = ['1_minute', '1_hour', '1_day', '1_month', '1_year']
            elif avg_time == '1_hour':
                period_avg_time = ['1_hour', '1_day', '1_month', '1_year']
            elif avg_time == '1_day':
                period_avg_time = ['1_day', '1_month', '1_year']
            elif avg_time == '1_month':
                period_avg_time = ['1_month', '1_year']
            elif avg_time == '1_year':
                period_avg_time = ['1_year']
        elif month_start != month_finish:
            period_avg_time = ['1_minute', '1_hour', '1_day', '1_month']
            if avg_time == '1_minute':
                period_avg_time = ['1_minute', '1_hour', '1_day', '1_month']
            elif avg_time == '1_hour':
                period_avg_time = ['1_hour', '1_day', '1_month']
            elif avg_time == '1_day':
                period_avg_time = ['1_day', '1_month']
            elif avg_time == '1_month':
                period_avg_time = ['1_month']
        elif day_start != day_finish:
            if avg_time == '1_minute':
                period_avg_time = ['1_minute', '1_hour', '1_day']
            elif avg_time == '1_hour':
                period_avg_time = ['1_hour', '1_day']
            elif avg_time == '1_day':
                period_avg_time = ['1_day']
    else:
        period_avg_time = [avg_time]
    return period_avg_time


def values_out(
        values, values_exel, source_id, measurand_id,
        method_processing, time_interval, time_obs, value_data
):

    # for parameter, value in zip(method_processing, value_data):
    value_float = 'NULL'
    value_text = 'NULL'
    if type(value_data) == float or type(value_data) == int:
        value_float = f"'{{{value_data}}}'"
        if type(values_exel) == list:
            values_exel.append([time_obs, source_id, measurand_id, method_processing, value_data])
    else:
        value_text = f"'{{{value_data}}}'"
    if type(values) == str:
        if values:
            values += ', '
        time_rec = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')
        values += sql_value_pattern.format(
            SOURCE_ID=source_id, MEASURAND_ID=measurand_id,
            METHOD_PROCESSING=method_processing,
            TIME_INTERVAL=time_interval,
            TIME_OBS=time_obs, TIME_REC=time_rec, VALUE_FLOAT=value_float, VALUE_TEXT=value_text
        )

    return values, values_exel


def conditions(source_id: str,  measurand_id: str, no_source_id: str,
               no_measurand_id: str):
    condition = None
    column = ['source_id', 'measurand_id']
    no = ['', 'not']
    n = 0
    k = 0
    for ids in [source_id, measurand_id, no_source_id, no_measurand_id]:
        if ids:
            if condition:
                condition += sql_id_condition.format(AND='and', COLUMN=column[n], NOT=no[k], ID_COLUMN=ids)
            else:
                condition = sql_id_condition.format(AND='', COLUMN=column[n], NOT=no[k], ID_COLUMN=ids)
        n += 1
        if n > 1:
            k += 1
            n = 0

    return condition
