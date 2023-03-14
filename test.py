from datetime import datetime
from dateutil.relativedelta import relativedelta


tNow = datetime.utcnow()
tFinish = tNow.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
tStart = tFinish - relativedelta(months=1)
print(tStart, tFinish)
date_after_month = datetime.utcnow() - relativedelta(day=1, month=2, year=2025)
print('Today: ', datetime.today().strftime('%d/%m/%Y'))
print('After Month:', date_after_month.strftime('%d/%m/%Y'))