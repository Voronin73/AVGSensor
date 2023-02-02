
def logs(start_dir: str):
    """Функция логирования ошибок выполнения скриптов"""
    import logging
    from time import gmtime, strftime
    logging.basicConfig(filename=start_dir + '/Logs/' + strftime("%d-%m-%Y", gmtime()) + ' Error.log',
                        filemode='a', format='%(asctime)s')
    logging.exception("ERROR")


def info(text: str, start_dir: str):
    """Функция логирования выполнения программы"""
    from time import gmtime, strftime
    with open(start_dir + '/Logs/' + strftime("%d-%m-%Y", gmtime()) + ' Info.log', 'a') as log:
        log.write(strftime("%d-%m-%Y %H:%M:%S", gmtime()) + ' - ' + text + '\n')
    print(strftime("%d-%m-%Y %H:%M:%S", gmtime()) + ' - ' + text)


def remove(start_dir: str, logs_old_dell: int):
    """Функция удаления старых лог файлов"""
    import os
    from time import gmtime, strftime, time
    current_time = time()
    log_dir = start_dir + '/Logs/'
    files = os.listdir(log_dir)
    for file in files:
        if (current_time - os.path.getctime(log_dir + file)) // 86400 >= logs_old_dell:
            os.remove(log_dir + file)
            with open(start_dir + '/Logs/' + strftime("%d-%m-%Y", gmtime()) + ' Info.log', 'a') as log:
                log.write(strftime("%d-%m-%Y %H:%M:%S", gmtime()) + ' - Выполнено удаление файла "' + file + '".\n')
            print(strftime("%d-%m-%Y %H:%M:%S", gmtime()) + ' - Выполнено удаление файла "' + file + '".')
