from pymongo import MongoClient

client = MongoClient("localhost", 27017)
db = client.data
student = db.students
marks = db.marks

for i in student.find({"batch": "2016", "sem": 5}):
    print(i["usn"])
