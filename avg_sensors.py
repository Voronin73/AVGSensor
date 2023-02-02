from log_files import info
from functions import sql_request, arguments
from constants import start_dir

# Press the green button in the gutter to run the script.

if __name__ == '__main__':

    """Для ручнного задания времяни введите дату и время окончания сбора данных, в формате 'YY-MM-DD HH:mm', 
       период в минутах (по умолчанию 1440 (сутки)), 
       время осреднения в минутах (по умолчанию 1 минутаб не должно превышать 48 часов), 
       количество строк(не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк). 
       Для атоматического задания времяни введите период в минутах (по умолчанию 1440 (сутки)),
       время осреднения в минутах (по умолчанию 1 минутаб не должно превышать 48 часов),
       количество строк (не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк)"""

    prev_days, start_time, finish_time, period, avg_time, col_string, timeout = arguments()

    # Раскоментировать и ввести необходимые параметры для ручного ввода
    #
    # start_time = '23-02-01 00:00:00'                        # Формат 'YY-MM-DD HH:mm'
    # finish_time = '23-01-31 00:00:00'    # Формат 'YY-MM-DD HH:mm'
    period = 60
    avg_time = 20
    # prev_days = 2

    result = sql_request(
        prev_days=prev_days, time_start=start_time, time_finish=finish_time, period=period,
        avg_time=avg_time, col_string=3000000, timeout=60
    )
    if result:
        info(
            f'Выполнена обработка данных с "{result[0]}" по "{result[1]}", '
            f'осреденеие данных "{result[2]} мин.", '
            f'затраченное время: "{result[3]}".', start_dir
        )
