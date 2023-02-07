from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side

from os.path import exists
from os import remove


def set_border(ws, cell_range):
    thin = Side(border_style='thin', color="000000")
    bold = Side(border_style='medium', color="000000")
    n = ws.max_row
    k = ws.max_column
    s = 1
    for row in ws[cell_range]:
        a = 1
        for cell in row:
            if s == 1:
                pass
            elif s == 2:
                cell.border = Border(top=bold, left=bold, right=bold, bottom=bold)
                cell.font = Font(bold='bold')
            elif a == 1 and s == n:
                cell.border = Border(top=thin, left=bold, right=thin, bottom=bold)
            elif a == 1:
                cell.border = Border(top=thin, left=bold, right=thin, bottom=thin)
            elif a == k and s == n:
                cell.border = Border(top=thin, left=thin, right=bold, bottom=bold)
            elif a == k:
                cell.border = Border(top=thin, left=thin, right=bold, bottom=thin)
            elif s == n:
                cell.border = Border(top=thin, left=thin, right=thin, bottom=bold)
            else:
                cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)
            cell.alignment = Alignment(horizontal='center')
            a += 1
        s += 1


def add_exel_files(data: list, avd_time: int, time_start, time_finish):

    sheet_name = f'AVG_sensor {avd_time} мин'
    file_name = f'{time_finish} {sheet_name}.xlsx'
    if exists(file_name):
        remove(file_name)
    book = Workbook()
    sheet = book.active
    sheet.title = sheet_name

    sheet.merge_cells('A1:G1')
    sheet['A1'] = f'Осреденение данных за {avd_time} мин. с "{time_start}" по "{time_finish}".'
    sheet['A1'].alignment = Alignment(horizontal='center')
    sheet['A1'].font = Font(bold='bold', italic=True, size=12)
    sheet.append(['Time_obs', 'Sourse_id', 'Measurand_id', 'Measurand_label',
                  'Method_processing', 'Value', 'Count'])
    n = 2
    for values in data:
        sheet.append(values)
        n += 1

    set_border(sheet, f'A1:G{n}')
    sheet.row_dimensions[1].font = Font(bold=True)

    sheet.column_dimensions['A'].width = 20

    sheet.column_dimensions['B'].width = 10
    sheet.column_dimensions['C'].width = 18
    sheet.column_dimensions['D'].width = 20
    sheet.column_dimensions['E'].width = 23
    sheet.column_dimensions['F'].width = 11
    sheet.column_dimensions['G'].width = 11

    filters = sheet.auto_filter
    filters.ref = f"A2:G{n}"
    book.save(file_name)
