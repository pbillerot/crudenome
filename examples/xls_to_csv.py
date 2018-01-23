#/usr/bin/python3
# -*- coding: utf-8 -*-
import xlrd
import csv
from os import sys

def csv_from_excel(excel_file):
    workbook = xlrd.open_workbook(excel_file)
    all_worksheets = workbook.sheet_names()
    for worksheet_name in all_worksheets:
        worksheet = workbook.sheet_by_name(worksheet_name)
        with open('{}.csv'.format(worksheet_name), 'w') as your_csv_file:
            wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)
            for rownum in range(worksheet.nrows):
                wr.writerow(worksheet.row_values(rownum))

def csv_from_excel2():

    wb = xlrd.open_workbook('your_workbook.xls')
    sh = wb.sheet_by_index(0)
    your_csv_file = open('your_csv_file.csv', 'wb')
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in xrange(sh.nrows):
        wr.writerow(sh.row_values(rownum))

    your_csv_file.close()

if __name__ == "__main__":
    csv_from_excel(sys.argv[1])