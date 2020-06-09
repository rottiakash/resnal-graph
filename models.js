var mongoose = require("mongoose");
var Schema = mongoose.Schema;

var StudentSchema = new Schema({
  totalFCD: String,
  name: String,
  usn: String,
  sem: Number,
  section: String,
  batch: String,
  gpa: Number,
});

var Student = mongoose.model("Student", StudentSchema);

var MarksSchema = new Schema({
  sid: String,
  subjectCode: String,
  subjectName: String,
  internalMarks: Number,
  externalMarks: Number,
  totalMarks: Number,
  result: String,
  fcd: String,
  grade: Number,
});

var Marks = mongoose.model("Marks", MarksSchema);

module.exports = { Student, Marks };
