import math
import datetime
import argparse
import sys

a, b = [3.9, 4.6, 4.0, 3.7, 3.4, 2.5, 2.8, 2.8, 3.2, 3.1, 3.0, 2.5, 2.3, 2.4, 2.2, 2.4, 2.8, 2.3, 2.0, 2.1, 2.3], [135.0, 140.6, 129.4, 118.1, 118.1, 140.6, 151.9, 140.6, 163.1, 163.1, 135.0, 140.6, 112.5, 146.3, 151.9, 123.8, 123.8, 146.3, 208.1, 191.3, 146.3]


def get_avg_direction(directions, speeds):
    sinSum = 0
    cosSum = 0
    speed = 0
    for value1, value2 in zip(directions, speeds):
        sinSum += math.sin(math.radians(value1))
        cosSum += math.cos(math.radians(value1))
        speed += value2
    return (math.degrees(math.atan2(sinSum, cosSum)) + 360) % 360, speed/len(speeds)


d, sp = get_avg_direction(a, b)

print(round(d, 3), round(sp, 3))


def get_avg_direction(directions, speeds):
    sinSum = 0.0
    cosSum = 0.0
    for value, speed in zip(directions, speeds):
        sinSum += speed * math.sin(math.radians(value))
        cosSum += speed * math.cos(math.radians(value))
    sinSum = sinSum / len(directions)
    cosSum = cosSum / len(directions)
    return ((math.degrees(math.atan2(sinSum, cosSum)) + 360) % 360), math.sqrt(cosSum**2 + sinSum**2)


d, sp = get_avg_direction(a, b)

print(round(d, 3), round(sp, 3))
t = datetime.datetime.utcnow()
k = 1440

print((datetime.datetime.min - t) % datetime.timedelta(minutes=k))
delta = t - datetime.timedelta(minutes=k) + (datetime.datetime.min - t) % datetime.timedelta(minutes=k)

print(t, delta)


def arguments():
    parser = argparse.ArgumentParser(
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
        help='Время начала осреднения данных в формате "YY-MM-DD HH:mm:SS". '
             'Не обязательный параметер.',
        metavar=': дата и время начала осреднения'
    )

    parser_group.add_argument(
        '-f', '--finish_time', type=str, default='',
        help='Время окончания осреднения данных в формате "YY-MM-DD HH:mm:SS". '
             'Если параметер не введен используется текущее время.',
        metavar=': дата и время окончания осреднения'
    )
    parser_group.add_argument(
        '-p', '--period', type=float, default=1440,
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

    namespace = parser.parse_args(sys.argv[1:])

    return namespace.start_time, namespace.finish_time, namespace.period,\
        namespace.avg_time, namespace.col_string, namespace.timeout


print(arguments())
