const { ApolloServer, gql } = require("apollo-server-express");
const mongoose = require("mongoose");
const express = require("express");
const { Student, Marks } = require("./models");
mongoose.connect("mongodb://localhost:27017/data", {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});
var db = mongoose.connection;
db.on("error", console.error.bind(console, "connection error:"));
db.once("open", function () {
  console.log("Connected to MongoDB Atlas");
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

  type Query {
    batchResult(
      batch: String
      sem: Int
      section: String
      yearBack: Boolean
    ): [Student]

    subjectWizeResult(
      batch: String
      sem: Int
      section: String
      yearBack: Boolean
      subjectCode: String
    ): [Student]
  }
`;

const resolvers = {
  Query: {
    batchResult: (parent, data) => {
      var query;
      filterSubs = false;
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

      const promise = query.exec();
      return promise;
    },
    subjectWizeResult: (parent, data) => {
      filterSubs = true;
      let query = data.section
        ? Student.find({
            sem: data.sem,
            batch: data.batch,
            section: data.section,
          })
        : Student.find({ sem: data.sem, batch: data.batch });
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
server.applyMiddleware({ app, path: "/" });
app.listen({ port: 4000 }, () =>
  console.log(`🚀 Server ready at http://localhost:4000${server.graphqlPath}`)
);

//* /results = list(filter(lambda x: ((int(x.usn[3:5])<batch2) or (int(x.usn[3:5])<=batch2 and int(x.usn[7:])>=400 )),results)) */
