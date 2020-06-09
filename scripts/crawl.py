import cv2
import numpy as np
import pytesseract
import xlrd
import requests
from lxml import html
import re
from pymongo import MongoClient
from bs4 import BeautifulSoup
import urllib3

client = MongoClient("localhost", 27017)
db = client.data
student = db.students
marks = db.marks
data = db.data

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

post_payload = {
    "Token": "55af47bae3a4104902c28cea54dcce98ae34318b",
    "captchacode": "iV4DKr",
}
post_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15",
    "Accept": "*/*",
    "Cache-Control": "no-cache",
    "Postman-Token": "864cb406-0cf9-4518-93aa-66023eef8e00",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://results.vtu.ac.in/_CBCS/resultpage.php?lns=1BI17CS010&captchacode=uFPXjv&Token=9da2da7349afd3ed906f17e8fbf3d284a55b29ba",
    "Connection": "keep-alive",
}

try:
    from PIL import Image
except ImportError:
    import Image


def getNewSession():
    url = "https://results.vtu.ac.in/_CBCS/index.php"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Postman-Token": "b222b1f1-1fed-4490-965a-805f53a28e97",
        "Host": "results.vtu.ac.in",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    response = requests.request("GET", url, headers=headers, verify=False)
    soup = BeautifulSoup(response.content, "html.parser")
    img_url = "https://results.vtu.ac.in" + (soup.find_all("img")[1])["src"]
    token = soup.find_all("input", attrs={"name": "Token"})
    post_payload["Token"] = token[0]["value"]
    img_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15",
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Postman-Token": "063fdb07-fe60-466a-be5e-fe08dec56a21",
        "Host": "results.vtu.ac.in",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    img_headers["Cookie"] = str(response.headers["Set-Cookie"]).rstrip("; path=/'")
    post_headers["Cookie"] = img_headers["Cookie"]
    response = requests.request("GET", img_url, headers=img_headers, verify=False)
    with open("cap.png", "wb") as file:
        file.write(response.content)
    image = cv2.imread("cap.png")
    result = image.copy()
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([-10, -10, 62])
    upper = np.array([10, 10, 142])
    mask = cv2.inRange(image, lower, upper)
    result = cv2.bitwise_and(result, result, mask=mask)
    cv2.imwrite("mask.png", mask)
    cv2.imwrite("out.png", image)
    cv2.imwrite("result.png", result)
    cv2.waitKey()
    post_payload["captchacode"] = pytesseract.image_to_string(Image.open("mask.png"))


def getResult(USN, sem):
    post_payload["lns"] = USN
    url = "https://results.vtu.ac.in/_CBCS/resultpage.php"
    res = requests.request(
        "POST", url, headers=post_headers, data=post_payload, verify=False
    )
    if "Invalid captcha code !!!" in res.text:
        print("Invalid Captcha, getting new session")
        getNewSession()
        return getResult(USN, sem)
    elif "Redirecting to VTU Results Site" in res.text:
        getNewSession()
        return getResult(USN, sem)
    elif "University Seat Number is not available or Invalid..!" in res.text:
        return 404
    elif "Invalid USN Format.." in res.text:
        return 404
    elif "Please check website after 4 hour --- !!!" in res.text:
        print("IP BLOCKED...CHECK PROXY...PRESS ANY KEY TO CONTINUE")
        input()
        getResult(USN, sem)
    elif "Semester : %d" % (sem) in res.text:
        soup = BeautifulSoup(res.content, "html.parser")
        result = [soup.find_all("td")[3].text.lstrip(" : ")]
        table = soup.find_all("div", attrs={"class": "divTable"})[0]
        rows = table.find_all("div", attrs={"class": "divTableRow"})[1:]
        for row in rows:
            sub = {}
            cells = row.find_all("div", attrs={"class": "divTableCell"})
            sub["subcode"] = cells[0].text
            sub["subname"] = cells[1].text
            sub["ia"] = cells[2].text
            sub["ea"] = cells[3].text
            sub["total"] = cells[4].text
            sub["result"] = cells[5].text
            result.append(sub)
        print(result)
        return result
    elif "Semester" in res.text:
        return 404
    else:
        getNewSession()
        return getResult(USN, sem)


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
    if subcode == "18MAT11":
        return 4
    if subcode == "18PHY12":
        return 4
    if subcode == "18ELE13":
        return 3
    if subcode == "18CIV14":
        return 3
    if subcode == "18EGDL15":
        return 3
    if subcode == "18PHYL16":
        return 1
    if subcode == "18ELEL17":
        return 1
    if subcode == "18EGH18":
        return 1
    if subcode == "18CS32":
        return 4
    elif re.search("^..[A-Z][A-Z][A-Z]?(L|P)[0-9][0-9]$", subcode) is not None:  # Lab
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


# Mongo Part
for s in data.find({"done": True}):
    USN = s["usn"]
    print("USN:-" + USN)
    stu = {
        "usn": USN,
        "section": s["sec"],
        "batch": str(int(s["batch"])),
        "sem": int(s["sem"]),
    }
    try:
        stu_id = student.insert_one(stu).inserted_id
    except:
        print("Student Data Already Exists")
        data.update({"_id": s["_id"]}, {"$set": {"done": True}})
        continue
    res = getResult(USN, s["sem"])
    if res == 404:
        print("USN Invalid")
        student.remove({"_id": stu_id})
        data.update({"_id": s["_id"]}, {"$set": {"done": True}})
        continue
    else:
        student.update({"_id": stu_id}, {"$set": {"name": res[0]}})
        print(res[0])
        res = res[1:]
        for r in res:
            mark = {
                "sid": str(stu_id),
                "subjectCode": r["subcode"],
                "subjectName": r["subname"],
                "internalMarks": r["ia"],
                "externalMarks": r["ea"],
                "totalMarks": r["total"],
                "result": r["result"],
            }
            marks.insert_one(mark)
        getGrade(USN, str(int(s["batch"])), s["sem"])
        FCD(USN, str(int(s["batch"])), s["sem"])
        totalFCD(USN, str(int(s["batch"])), s["sem"])
        GPA(USN, str(int(s["batch"])), s["sem"])
        data.update({"_id": s["_id"]}, {"$set": {"done": True}})
print("Done")
