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

from openpyxl.workbook import Workbook

headers       = ['Company','Address','Tel','Web']
workbook_name = 'sample.xlsx'
wb = Workbook()
page = wb.active
page.title = 'companies'
page.append(headers) # write the headers to the first line

# Data to write:
companies = [['name1','address1','tel1','web1'], ['name2','address2','tel2','web2']]

for info in companies:
    page.append(info)
wb.save(filename = workbook_name)
type(None)