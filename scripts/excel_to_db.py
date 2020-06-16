import xlrd
import json
from pymongo import MongoClient
import re

client = MongoClient("localhost", 27017)
db = client.data
student = db.students
marks = db.marks

# Helper Methods


def getGrade(USN, batch, sem):
    selected_student = student.find({"usn": USN, "batch": batch, "sem": sem})[0]
    for i in marks.find({"sid": str(selected_student["_id"])}):
        grade = 0
        if int(i["totalMarks"]) >= 90:
            grade = 10
        elif 80 <= int(i["totalMarks"]) <= 89:
            grade = 9
        elif 70 <= int(i["totalMarks"]) <= 79:
            grade = 8
        elif 60 <= int(i["totalMarks"]) <= 69:
            grade = 7
        elif 50 <= int(i["totalMarks"]) <= 59:
            grade = 6
        elif 45 <= int(i["totalMarks"]) <= 49:
            grade = 5
        elif 40 <= int(i["totalMarks"]) <= 44:
            grade = 4
        elif int(i["totalMarks"]) < 40:
            grade = 0
        marks.update_one({"_id": i["_id"]}, {"$set": {"grade": grade}})


def totalFCD(USN, batch, sem):
    selected_student = student.find({"usn": USN, "batch": batch, "sem": sem})[0]
    total = 0
    FCD = ""
    for j in marks.find({"sid": str(selected_student["_id"])}):
        if j["fcd"] == "F":
            student.update_one(
                {"_id": selected_student["_id"]}, {"$set": {"totalFCD": "F"}}
            )
            return
        total += int(j["totalMarks"])
    if total >= 560:
        FCD = "FCD"
    elif 480 <= total <= 559:
        FCD = "FC"
    elif 400 <= total <= 499:
        FCD = "SC"
    else:
        FCD = "P"
    student.update_one({"_id": selected_student["_id"]}, {"$set": {"totalFCD": FCD}})


def FCD(USN, batch, sem):
    selected_student = student.find({"usn": USN, "batch": batch, "sem": sem})[0]
    for i in marks.find({"sid": str(selected_student["_id"])}):
        if i["result"] == "F" or i["result"] == "A" or i["result"] == "X":
            FCD = "F"
        else:
            if 70 <= int(i["totalMarks"]) <= 100:
                FCD = "FCD"
            elif 60 <= int(i["totalMarks"]) <= 69:
                FCD = "FC"
            elif 50 <= int(i["totalMarks"]) <= 59:
                FCD = "SC"
            elif 40 <= int(i["totalMarks"]) <= 49:
                FCD = "P"
            else:
                FCD = "F"
        marks.update_one({"_id": i["_id"]}, {"$set": {"fcd": FCD}})


def GPA(USN, batch, sem):
    selected_student = student.find({"usn": USN, "batch": batch, "sem": sem})[0]
    totalgrade = 0
    totalCredit = 0
    gpa = 0
    roundoff = 0
    for j in marks.find({"sid": str(selected_student["_id"])}):
        totalgrade += j["grade"] * getCredit(j["subjectCode"])
        totalCredit += 10 * getCredit(j["subjectCode"])
    gpa = (totalgrade / totalCredit) * 10
    roundoff = round(gpa, 2)
    student.update_one({"_id": selected_student["_id"]}, {"$set": {"gpa": roundoff}})


def getCredit(subcode):
    if re.search("^..[A-Z][A-Z][A-Z]?(L|P)[0-9][0-9]$", subcode) is not None:  # Lab
        return 2
    elif re.search("^18[A-Z][A-Z][A-Z]?[0-9][0-9]$", subcode) is not None:  # Subject
        return 3
    elif (
        re.search("^(15|16|17)[A-Z][A-Z][A-Z]?[0-9][0-9]$", subcode) is not None
    ):  # Subject
        return 4
    elif (
        re.search("^..[A-Z][A-Z][A-Z]?[0-9][0-9][0-9]$", subcode) is not None
    ):  # Elective
        return 3
    elif re.search("^..MATDIP[0-9][0-9]$", subcode) is not None:  # MATDIP
        return 0


book = xlrd.open_workbook("./2016-6th.xlsx")
first_sheet = book.sheet_by_index(0)
i = 2
result = []
while True:
    if first_sheet.cell_value(i, 0) == "end":
        break
    USN = first_sheet.cell_value(i, 1)
    batch = 2016
    sec = first_sheet.cell_value(i, 2)
    name = first_sheet.cell_value(i, 0)
    sem = 6
    subs = [
        {"name": "Cryptography, Network Security and Cyber Law", "code": "15CS61"},
        {"name": "Computer Graphics and Visualization", "code": "15CS62"},
        {"name": "System Software and Compiler Design", "code": "15CS63"},
        {"name": "Operating Systems", "code": "15CS64"},
        {"name": "Data Mining and Data Warehousing", "code": "15CS651"},
        {"name": "Operations research", "code": "15CS653"},
        {"name": "Python Application Programming", "code": "15CS664"},
        {
            "name": "System Software and Operating System -- Laboratory",
            "code": "15CSL67",
        },
        {"name": "Computer Graphics Laboratory with mini project", "code": "15CSL68"},
        {"name": "Value engineering", "code": "15IM663"},
        {"name": "Linear Algebra", "code": "15MAT661"},
    ]
    d = {"usn": USN, "name": name, "batch": batch, "sec": sec, "sem": sem, "marks": []}
    for j in range(0, 10):
        increment = 4 * j
        try:
            ia = int(first_sheet.cell_value(i, 3 + increment))
        except:
            continue
        ea = int(first_sheet.cell_value(i, 4 + increment))
        total = int(first_sheet.cell_value(i, 5 + increment))
        res = first_sheet.cell_value(i, 6 + increment)
        if not res == "F":
            res = "P"
        mark = {
            "name": subs[j]["name"],
            "code": subs[j]["code"],
            "ia": ia,
            "ea": ea,
            "total": total,
            "res": res,
        }
        d["marks"].append(mark)
    result.append(d)
    i += 1
print("Done")
print(json.dumps(result, indent=4))
# Mongo Part

for s in result:
    USN = s["usn"]
    print("USN:-" + USN)
    stu = {
        "usn": USN,
        "name": s["name"],
        "section": s["sec"],
        "batch": str(int(s["batch"])),
        "sem": int(s["sem"]),
    }
    stu_id = student.insert_one(stu).inserted_id
    for r in s["marks"]:
        mark = {
            "sid": str(stu_id),
            "subjectCode": r["code"],
            "subjectName": r["name"],
            "internalMarks": r["ia"],
            "externalMarks": r["ea"],
            "totalMarks": r["total"],
            "result": r["res"],
        }
        marks.insert_one(mark)
        getGrade(USN, str(int(s["batch"])), s["sem"])
        FCD(USN, str(int(s["batch"])), s["sem"])
        totalFCD(USN, str(int(s["batch"])), s["sem"])
        GPA(USN, str(int(s["batch"])), s["sem"])
print("dumped")
