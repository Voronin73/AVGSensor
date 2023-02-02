from log_files import info
from functions import sql_request, arguments
from constants import start_dir


# Press the green button in the gutter to run the script.

if __name__ == '__main__':

    """Для ручнного задания времяни введите дату и время окончания сбора данных, в формате 'YYYY-MM-DD HH:mm:SS', 
       период в минутах (по умолчанию 1440 (сутки)), 
       время осреднения в минутах (по умолчанию 1 минутаб не должно превышать 48 часов), 
       количество строк(не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк). 
       Для атоматического задания времяни введите период в минутах (по умолчанию 1440 (сутки)),
       время осреднения в минутах (по умолчанию 1 минутаб не должно превышать 48 часов),
       количество строк (не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк)"""

    start_time, finish_time, period, avg_time, col_string, timeout = arguments()

    #
    #
    # start_time = ''                        # Формат 'YY-MM-DD HH:mm:SS'
    # finish_time = '23-01-31 00:00:00'    # Формат 'YY-MM-DD HH:mm:SS'
    # period = 60*24
    # avg_time = 60

    result = sql_request(
        time_start=start_time, time_finish=finish_time, period=period,
        avg_time=avg_time, col_string=3000000, timeout=60
    )
    if result:
        info(
            f'Выполнена обработка данных с "{result[0]}" по "{result[1]}", '
            f'осреденеие данных "{result[2]} мин.", '
            f'затраченное время: "{result[3]}".', start_dir
        )
