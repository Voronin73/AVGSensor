from log_files import info
from functions import arguments
from constants import start_dir
from avg import avg


# Press the green button in the gutter to run the script.

if __name__ == '__main__':

    """Для ручнного задания времяни введите дату и время окончания сбора данных, в формате 'YYYY-MM-DD HH:mm'"""

    start_time, finish_time, auto, avg_time, col_string, timeout, source_id, no_source_id,\
        measurand_id, no_measurand_id, sql_table, exel = arguments()

    # Раскоментировать и ввести необходимые параметры для ручного ввода
    #
    start_time = '2023-01-05 00:00'     # Формат 'YY-MM-DD HH:mm'
    finish_time = '2023-02-01 00:00'    # Формат 'YY-MM-DD HH:mm'
    # avg_time = '1_minute'
    # source_id = [39]
    # measurand_id = [52]
    # no_source_id = [1,2,3]
    # no_measurand_id = [52, 181]
    sql_table = 1


    result = avg(
        time_start=start_time, time_finish=finish_time, auto=auto,
        avg_time=avg_time, source=source_id, no_source=no_source_id, measurand=measurand_id,
        no_measurand=no_measurand_id, sql_table=sql_table, exel=exel, col_string=col_string, timeout=timeout
    )
    if result:
        info(
            f'Выполнена обработка данных с "{result[0]}" по "{result[1]}", '
            f'осреденеие данных "{result[2]} мин.", '
            f'затраченное время: "{result[3]}".', start_dir
        )
