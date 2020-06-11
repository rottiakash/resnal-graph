from flask import Flask, request, send_file, Response
import sys
from pymongo import MongoClient
import xlsxwriter

client = MongoClient("localhost", 27017)
db = client.data
student = db.students
marks = db.marks
app = Flask(__name__)


@app.route("/script/batchwize")
def batchwize():
    cFCD = 0
    cFC = 0
    cSC = 0
    cP = 0
    cF = 0
    passCount = 0
    failCount = 0
    batch = str(request.args.get("batch"))
    sem = int(request.args.get("sem"))
    query = {"batch": batch, "sem": sem}
    workbook = xlsxwriter.Workbook("../Public/%s-%s_Sem.xlsx" % (batch, sem))
    if request.args.get("sec"):
        sec = str(request.args.get("sec"))
        query["section"] = sec
        workbook = xlsxwriter.Workbook(
            "../Public/%s-%s_Sem-%s_Sec.xlsx" % (batch, sem, sec)
        )
    worksheet = workbook.add_worksheet()
    heading = workbook.add_format({"bold": True, "border": 1})
    worksheet.write(0, 0, "Student Name", heading)
    worksheet.write(0, 1, "Student USN", heading)
    worksheet.write(0, 2, "Section", heading)
    worksheet.write(0, 3, "GPA", heading)
    merge_format = workbook.add_format({"align": "center", "bold": True, "border": 1})
    worksheet.merge_range("E1:F1", "Overall Grade", merge_format)
    border_format = workbook.add_format({"border": 1})
    border_format_fcd_green = workbook.add_format(
        {"align": "center", "border": 1, "bg_color": "green"}
    )
    border_format_fcd_blue = workbook.add_format(
        {"align": "center", "border": 1, "bg_color": "blue"}
    )
    border_format_fcd_yellow = workbook.add_format(
        {"align": "center", "border": 1, "bg_color": "yellow"}
    )
    border_format_fcd_purple = workbook.add_format(
        {"align": "center", "border": 1, "bg_color": "purple"}
    )
    border_format_fcd_red = workbook.add_format(
        {"align": "center", "border": 1, "bg_color": "red"}
    )
    j = 1
    for i in student.find(query).sort("gpa", -1):
        if i["totalFCD"] == "F" or i["totalFCD"] == "A" or i["totalFCD"] == "X":
            failCount += 1
        else:
            passCount += 1
        if i["totalFCD"] == "FCD":
            fcd_format = border_format_fcd_green
            cFCD = cFCD + 1
        elif i["totalFCD"] == "FC":
            fcd_format = border_format_fcd_blue
            cFC = cFC + 1
        elif i["totalFCD"] == "SC":
            fcd_format = border_format_fcd_yellow
            cSC = cSC + 1
        elif i["totalFCD"] == "P":
            fcd_format = border_format_fcd_purple
            cP = cP + 1
        elif i["totalFCD"] == "F":
            fcd_format = border_format_fcd_red
            cF += 1
        worksheet.write(j, 0, i["name"], border_format)
        worksheet.write(j, 1, i["usn"], border_format)
        worksheet.write(j, 2, i["section"], border_format)
        worksheet.write(j, 3, i["gpa"], border_format)
        worksheet.merge_range(j, 4, j, 5, i["totalFCD"], fcd_format)
        j = j + 1
    worksheet.write("O4", "FCD", heading)
    worksheet.write("P4", "FC", heading)
    worksheet.write("Q4", "SC", heading)
    worksheet.write("R4", "P", heading)
    worksheet.write("S4", "F", heading)
    worksheet.write("O5", cFCD, border_format)
    worksheet.write("P5", cFC, border_format)
    worksheet.write("Q5", cSC, border_format)
    worksheet.write("R5", cP, border_format)
    worksheet.write("S5", cF, border_format)
    chart = workbook.add_chart({"type": "column"})
    data = ["FCD", "FC", "SC", "P", "F"]
    chart.add_series(
        {
            "data_labels": {"value": True, "position": "inside_end"},
            "categories": "=Sheet1!$O$4:$S$4",
            "values": "=Sheet1!$O$5:$S$5",
        }
    )
    chart.set_legend({"none": True})
    worksheet.insert_chart("O9", chart)
    worksheet.write("O26", "Pass", heading)
    worksheet.write("P26", "Fail", heading)
    worksheet.write("O27", int(passCount), border_format)
    worksheet.write("P27", int(failCount), border_format)
    Pchart = workbook.add_chart({"type": "pie"})
    Pchart.add_series(
        {
            "data_labels": {
                "value": True,
                "category": True,
                "separator": "\n",
                "position": "center",
            },
            "categories": "=Sheet1!$O$26:$P$26",
            "values": "=Sheet1!$O$27:$P$27",
            "points": [{"fill": {"color": "green"}}, {"fill": {"color": "red"}},],
        }
    )
    worksheet.insert_chart("O31", Pchart)
    workbook.close()
    status_code = Response(status=200)
    return status_code


@app.route("/script/subjectwize")
def subjectWize():
    cFCD = 0
    cFC = 0
    cSC = 0
    cP = 0
    cF = 0
    passCount = 0
    failCount = 0
    batch = str(request.args.get("batch"))
    sem = int(request.args.get("sem"))
    subjectCode = str(request.args.get("sub"))
    query = {"batch": batch, "sem": sem}
    workbook = xlsxwriter.Workbook(
        "../public/%s-%s_Sem-%s.xlsx" % (batch, sem, subjectCode)
    )
    if request.args.get("sec"):
        sec = str(request.args.get("sec"))
        query["section"] = sec
        workbook = xlsxwriter.Workbook(
            "../public/%s-%s_Sem-%s_Sec-%s.xlsx" % (batch, sem, sec, subjectCode)
        )
    s = student.find(query)
    result = []
    for stud in s:
        d = {"name": stud["name"], "usn": stud["usn"], "section": stud["section"]}
        d["marks"] = marks.find_one(
            {"sid": str(stud["_id"]), "subjectCode": subjectCode}
        )
        result.append(d)
    worksheet = workbook.add_worksheet()
    heading = workbook.add_format({"bold": True, "border": 1})
    worksheet.write(0, 0, "Student Name", heading)
    worksheet.write(0, 1, "Student USN", heading)
    worksheet.write(0, 2, "Section", heading)
    merge_format = workbook.add_format({"align": "center", "bold": True, "border": 1})
    border_format = workbook.add_format({"border": 1})
    border_format_fcd_green = workbook.add_format({"border": 1, "bg_color": "green"})
    border_format_fcd_blue = workbook.add_format({"border": 1, "bg_color": "blue"})
    border_format_fcd_yellow = workbook.add_format({"border": 1, "bg_color": "yellow"})
    border_format_fcd_purple = workbook.add_format({"border": 1, "bg_color": "purple"})
    border_format_fcd_red = workbook.add_format({"border": 1, "bg_color": "red"})
    sname = ""
    index = 0
    try:
        if result[index]["marks"]:
            sname = result[index]["marks"]["subjectName"]
        else:
            index += 1
    except:
        pass
    worksheet.merge_range("D1:G1", sname, merge_format)
    worksheet.write(1, 3, "Internal Marks", heading)
    worksheet.write(1, 4, "External Marks", heading)
    worksheet.write(1, 5, "Total Marks", heading)
    worksheet.write(1, 6, "Class", heading)
    j = 2
    for i in result:
        if i["marks"]:
            if i["marks"]["fcd"] == "FCD":
                fcd_format = border_format_fcd_green
                cFCD = cFCD + 1
                passCount += 1
            elif i["marks"]["fcd"] == "FC":
                fcd_format = border_format_fcd_blue
                cFC = cFC + 1
                passCount += 1
            elif i["marks"]["fcd"] == "SC":
                fcd_format = border_format_fcd_yellow
                cSC = cSC + 1
                passCount += 1
            elif i["marks"]["fcd"] == "P":
                fcd_format = border_format_fcd_purple
                cP = cP + 1
                passCount += 1
            elif i["marks"]["fcd"] == "F":
                fcd_format = border_format_fcd_red
                cF = cF + 1
                failCount += 1
            worksheet.write(j, 0, i["name"], border_format)
            worksheet.write(j, 1, i["usn"], border_format)
            worksheet.write(j, 2, i["section"], border_format)
            worksheet.write(j, 3, i["marks"]["internalMarks"], border_format)
            worksheet.write(j, 4, i["marks"]["externalMarks"], border_format)
            worksheet.write(j, 5, i["marks"]["totalMarks"], border_format)
            worksheet.write(j, 6, i["marks"]["fcd"], fcd_format)
            j = j + 1
    worksheet.write("O4", "FCD", heading)
    worksheet.write("P4", "FC", heading)
    worksheet.write("Q4", "SC", heading)
    worksheet.write("R4", "P", heading)
    worksheet.write("S4", "F", heading)
    worksheet.write("O5", cFCD, border_format)
    worksheet.write("P5", cFC, border_format)
    worksheet.write("Q5", cSC, border_format)
    worksheet.write("R5", cP, border_format)
    worksheet.write("S5", cF, border_format)
    chart = workbook.add_chart({"type": "column"})
    data = ["FCD", "FC", "SC", "P", "F"]
    chart.add_series(
        {
            "data_labels": {"value": True, "position": "inside_end"},
            "categories": "=Sheet1!$O$4:$S$4",
            "values": "=Sheet1!$O$5:$S$5",
        }
    )
    chart.set_legend({"none": True})
    worksheet.insert_chart("O9", chart)
    worksheet.write("O26", "Pass", heading)
    worksheet.write("P26", "Fail", heading)
    worksheet.write("O27", int(passCount), border_format)
    worksheet.write("P27", int(failCount), border_format)
    Pchart = workbook.add_chart({"type": "pie"})
    Pchart.add_series(
        {
            "data_labels": {
                "value": True,
                "category": True,
                "separator": "\n",
                "position": "center",
            },
            "categories": "=Sheet1!$O$26:$P$26",
            "values": "=Sheet1!$O$27:$P$27",
            "points": [{"fill": {"color": "green"}}, {"fill": {"color": "red"}},],
        }
    )
    worksheet.insert_chart("O31", Pchart)
    workbook.close()
    status_code = Response(status=200)
    return status_code


app.run(host="0.0.0.0", debug=True)
