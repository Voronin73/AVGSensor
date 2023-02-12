from log_files import info
from functions import sql_request, arguments
from constants import start_dir
from settings import measurand_labels_not_avg

# Press the green button in the gutter to run the script.

if __name__ == '__main__':

    """Для ручнного задания времяни введите дату и время окончания сбора данных, в формате 'YY-MM-DD HH:mm', 
       период в минутах (по умолчанию 1440 (сутки)), 
       время осреднения в минутах (по умолчанию 1 минутаб не должно превышать 48 часов), 
       количество строк(не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк). 
       Для атоматического задания времяни введите период в минутах (по умолчанию 1440 (сутки)),
       время осреднения в минутах (по умолчанию 1 минута, не должно превышать 48 часов),
       количество строк (не обязательный параметр по умолчанию 3000, чем больше интервал тем больше количестао строк)"""

    prev_days, start_time, finish_time, period, avg_time, col_string, timeout, source_id, no_source_id,\
        measurand_id, no_measurand_id, measurand_label, no_measurand_label, sql_table, exel = arguments()
    # print(source_id, no_source_id, measurand_id, no_measurand_id, measurand_label, no_measurand_label)
    #
    # print(measurand_labels_not_avg)
    # Раскоментировать и ввести необходимые параметры для ручного ввода
    #
    # start_time = '23-02-01 00:00'                        # Формат 'YY-MM-DD HH:mm'
    # finish_time = '23-02-02 00:00'    # Формат 'YY-MM-DD HH:mm'
    period = 1
    avg_time = 1
    # prev_days = 3
    # source_id = [177166, 29, 28]
    # measurand_id = [181, 52]
    sql_table = 1


    result = sql_request(
        prev_days=prev_days, time_start=start_time, time_finish=finish_time, period=period,
        avg_time=avg_time, source_id=source_id, no_source_id=no_source_id, measurand_id=measurand_id,
        no_measurand_id=no_measurand_id, measurand_label=measurand_label, sql_table=sql_table, exel=exel,
        no_measurand_label=no_measurand_label, col_string=3000000, timeout=60
    )
    if result:
        info(
            f'Выполнена обработка данных с "{result[0]}" по "{result[1]}", '
            f'осреденеие данных "{result[2]} мин.", '
            f'затраченное время: "{result[3]}".', start_dir
        )
