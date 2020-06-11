const { ApolloServer, gql } = require("apollo-server-express");
const mongoose = require("mongoose");
const express = require("express");
const { Student, Marks } = require("./models");
const axios = require("axios");
var path = require("path");
const { resolve } = require("path");
var backlogList = [];
var batches = [];
mongoose.connect("mongodb://rottiakash.ddns.net:27017/data", {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});
var db = mongoose.connection;
db.on("error", console.error.bind(console, "connection error:"));
db.once("open", function () {
  console.log("Connected to MongoDB");
  Student.find({}).exec((err, docs) => {
    docs.map((doc) => {
      batches.push(doc.batch);
      if (doc.totalFCD == "F" || doc.totalFCD == "A" || doc.totalFCD == "X")
        backlogList.push(doc.usn);
    });
    batches = [...new Set(batches)];
    backlogList = [...new Set(backlogList)];
    console.log("In Memory Cache ready");
  });
});

var subcode;
var filterSubs;
const typeDefs = gql`
  type Student {
    id: ID
    totalFCD: String
    name: String
    usn: String
    sem: Int
    section: String
    batch: String
    gpa: Float
    marks: [Marks]
  }

  type Marks {
    id: ID
    sid: ID
    subjectCode: String
    subjectName: String
    internalMarks: Int
    externalMarks: Int
    totalMarks: Int
    fcd: String
    result: String
    grade: Float
  }

  type Subject {
    subjectName: String
    subjectCode: String
  }

  type Query {
    batchResult(
      batch: String
      sem: Int
      section: String
      yearBack: Boolean
      backLog: Boolean
    ): [Student]

    subjectWizeResult(
      batch: String
      sem: Int
      section: String
      yearBack: Boolean
      subjectCode: String
      backLog: Boolean
    ): [Student]

    batches: [String]
    sems(batch: String): [String]
    subs(batch: String, sem: Int): [Subject]
  }
`;

const resolvers = {
  Query: {
    subs: (parent, data) => {
      var promise = new Promise((resolve, reject) => {
        Student.find({ batch: data.batch, sem: data.sem })
          .exec()
          .then((students) => {
            var ids = [];
            students.map((student) => ids.push(student._id.toString()));
            Marks.aggregate([
              { $match: { sid: { $in: ids } } },
              {
                $group: {
                  _id: "$subjectCode",
                  subjectCode: { $first: "$subjectCode" },
                  subjectName: { $first: "$subjectName" },
                },
              },
            ])
              .sort("-subjectCode")
              .exec()
              .then((docs) => resolve(docs));
          });
      });

      return promise;
    },
    sems: (parent, data) => {
      var promise = new Promise((resolve, reject) => {
        var sems = [];
        Student.find({ batch: data.batch }).exec((err, docs) => {
          docs.map((doc) => sems.push(doc.sem));
          sems = [...new Set(sems)];
          resolve(sems);
        });
      });
      return promise;
    },
    batches: (parent, data) => batches,
    batchResult: (parent, data) => {
      var query;
      filterSubs = false;
      if (data.backLog) {
        query = data.section
          ? Student.find({
              usn: { $in: backlogList },
              sem: data.sem,
              batch: data.batch,
              section: data.section,
            }).sort("-gpa")
          : Student.find({
              usn: { $in: backlogList },
              sem: data.sem,
              batch: data.batch,
            }).sort("-gpa");
      } else {
        if (data.yearBack)
          query = data.section
            ? Student.find({
                sem: data.sem,
                batch: data.batch,
                section: data.section,
              }).sort("-gpa")
            : Student.find({ sem: data.sem, batch: data.batch }).sort("-gpa");
        else
          query = data.section
            ? Student.aggregate([
                {
                  $project: {
                    name: 1,
                    sem: 1,
                    section: 1,
                    totalFCD: 1,
                    usn: 1,
                    gpa: 1,
                    batch: 1,
                    isback: {
                      $or: [
                        {
                          $lt: [
                            { $substr: ["$usn", 3, 2] },
                            data.batch.slice(2, 4),
                          ],
                        },
                        {
                          $and: [
                            {
                              $lte: [
                                { $substr: ["$usn", 3, 2] },
                                data.batch.slice(2, 4),
                              ],
                            },
                            { $gte: [{ $substr: ["$usn", 7, 3] }, "400"] },
                          ],
                        },
                      ],
                    },
                  },
                },
                {
                  $match: {
                    backLog: data.backLog ? true : null,
                    isback: false,
                    batch: data.batch,
                    sem: data.sem,
                    section: data.section,
                  },
                },
              ]).sort("-gpa")
            : Student.aggregate([
                {
                  $project: {
                    name: 1,
                    sem: 1,
                    section: 1,
                    totalFCD: 1,
                    usn: 1,
                    gpa: 1,
                    batch: 1,
                    isback: {
                      $or: [
                        {
                          $lt: [
                            { $substr: ["$usn", 3, 2] },
                            data.batch.slice(2, 4),
                          ],
                        },
                        {
                          $and: [
                            {
                              $lte: [
                                { $substr: ["$usn", 3, 2] },
                                data.batch.slice(2, 4),
                              ],
                            },
                            { $gte: [{ $substr: ["$usn", 7, 3] }, "400"] },
                          ],
                        },
                      ],
                    },
                  },
                },
                {
                  $match: {
                    isback: false,
                    batch: data.batch,
                    sem: data.sem,
                  },
                },
              ]).sort("-gpa");
      }
      const promise = query.exec();
      return promise;
    },
    subjectWizeResult: (parent, data) => {
      filterSubs = true;
      if (data.backLog) {
        query = data.section
          ? Student.find({
              usn: { $in: backlogList },
              sem: data.sem,
              batch: data.batch,
              section: data.section,
            })
          : Student.find({
              usn: { $in: backlogList },
              sem: data.sem,
              batch: data.batch,
            });
      } else {
        if (data.yearBack)
          query = data.section
            ? Student.find({
                sem: data.sem,
                batch: data.batch,
                section: data.section,
              }).sort("-gpa")
            : Student.find({ sem: data.sem, batch: data.batch });
        else
          query = data.section
            ? Student.aggregate([
                {
                  $project: {
                    name: 1,
                    sem: 1,
                    section: 1,
                    totalFCD: 1,
                    usn: 1,
                    gpa: 1,
                    batch: 1,
                    isback: {
                      $or: [
                        {
                          $lt: [
                            { $substr: ["$usn", 3, 2] },
                            data.batch.slice(2, 4),
                          ],
                        },
                        {
                          $and: [
                            {
                              $lte: [
                                { $substr: ["$usn", 3, 2] },
                                data.batch.slice(2, 4),
                              ],
                            },
                            { $gte: [{ $substr: ["$usn", 7, 3] }, "400"] },
                          ],
                        },
                      ],
                    },
                  },
                },
                {
                  $match: {
                    backLog: data.backLog ? true : null,
                    isback: false,
                    batch: data.batch,
                    sem: data.sem,
                    section: data.section,
                  },
                },
              ])
            : Student.aggregate([
                {
                  $project: {
                    name: 1,
                    sem: 1,
                    section: 1,
                    totalFCD: 1,
                    usn: 1,
                    gpa: 1,
                    batch: 1,
                    isback: {
                      $or: [
                        {
                          $lt: [
                            { $substr: ["$usn", 3, 2] },
                            data.batch.slice(2, 4),
                          ],
                        },
                        {
                          $and: [
                            {
                              $lte: [
                                { $substr: ["$usn", 3, 2] },
                                data.batch.slice(2, 4),
                              ],
                            },
                            { $gte: [{ $substr: ["$usn", 7, 3] }, "400"] },
                          ],
                        },
                      ],
                    },
                  },
                },
                {
                  $match: {
                    isback: false,
                    batch: data.batch,
                    sem: data.sem,
                  },
                },
              ]);
      }
      subcode = data.subjectCode;
      var promise = query.exec();
      return promise;
    },
  },
  Student: {
    marks: (parent, data) => {
      const query = filterSubs
        ? Marks.find({ sid: parent._id, subjectCode: subcode })
        : Marks.find({ sid: parent._id });
      const promise = query.exec();
      return promise;
    },
  },
};

const server = new ApolloServer({
  typeDefs,
  resolvers,
});
const app = express();
app.get(
  "/script/subjectwize/:batch/:sem/:sub/:yearback/:backlog/:sec?",
  (req, res) => {
    axios
      .get("http://0.0.0.0:5000/script/subjectwize", {
        params: {
          ...req.params,
        },
      })
      .then(function (response) {
        if (!req.params.sec)
          res.download(
            path.join(
              __dirname,
              `/public/${req.params.batch}-${req.params.sem}_Sem-${req.params.sub}.xlsx`
            )
          );
        else
          res.download(
            path.join(
              __dirname,
              `/public/${req.params.batch}-${req.params.sem}_Sem-${req.params.sec}_Sec-${req.params.sub}.xlsx`
            )
          );
      });
  }
);
app.get(
  "/script/batchwize/:batch/:sem/:yearback/:backlog/:sec?",
  (req, res) => {
    axios
      .get("http://0.0.0.0:5000/script/batchwize", {
        params: {
          ...req.params,
        },
      })
      .then(function (response) {
        if (!req.params.sec)
          res.download(
            path.join(
              __dirname,
              `/public/${req.params.batch}-${req.params.sem}_Sem.xlsx`
            )
          );
        else
          res.download(
            path.join(
              __dirname,
              `/public/${req.params.batch}-${req.params.sem}_Sem-${req.params.sec}_Sec.xlsx`
            )
          );
      });
  }
);

server.applyMiddleware({ app, path: "/" });
app.listen({ port: 4000 }, () =>
  console.log(`🚀 Server ready at http://localhost:4000${server.graphqlPath}`)
);
