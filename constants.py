from sys import platform
from os import curdir, path, mkdir

if platform == "win32":
    sl = '\\'
else:
    sl = '/'

start_dir = path.abspath(curdir)
if not path.exists(start_dir + sl + 'Logs'):
    mkdir(start_dir + sl + 'Logs')
# local_dir = f'{start_dir}{sl}Data_base'
# reg_path = r"SOFTWARE\Oleg_Scripts\Presentations"
