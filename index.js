const { ApolloServer, gql } = require("apollo-server-express");
const mongoose = require("mongoose");
const express = require("express");
const { Student, Marks } = require("./models");
mongoose.connect(
  "mongodb+srv://admin:V0AzLuctQCCBY762@cluster0-dxbah.mongodb.net/test?retryWrites=true&w=majority",
  { useNewUrlParser: true, useUnifiedTopology: true }
);
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
      filterSubs = false;
      const query = data.section
        ? Student.find({
            sem: data.sem,
            batch: data.batch,
            section: data.section,
          })
        : Student.find({ sem: data.sem, batch: data.batch });
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
        ? Marks.find({ sid: parent.id, subjectCode: subcode })
        : Marks.find({ sid: parent.id });
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
