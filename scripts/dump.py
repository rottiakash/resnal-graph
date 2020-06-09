import xlrd
from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.data
data = db.data

book = xlrd.open_workbook("data.xlsx")
first_sheet = book.sheet_by_index(0)
i = 1

while True:
    if first_sheet.cell_value(i, 0) == "end":
        break
    USN = first_sheet.cell_value(i, 0)
    batch = first_sheet.cell_value(i, 1)
    sec = first_sheet.cell_value(i, 2)
    sem = first_sheet.cell_value(i, 3)
    print("USN:-" + first_sheet.cell_value(i, 0))
    d = {"usn": USN, "batch": batch, "sec": sec, "sem": sem, "done": False}
    data.insert_one(d)
    i += 1
print("Done")
