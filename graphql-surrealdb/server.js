// const express = require('express');
// const { graphqlHTTP } = require('express-graphql');
// const { buildSchema } = require('graphql');
// const { initDB, getPostById, getAllPosts } = require('./db');

import express from 'express';
import { graphqlHTTP } from 'express-graphql';
import { buildSchema } from 'graphql';
import { initDB, getPostById, getAllPosts } from './db.js';

const schema = buildSchema(`
  type Query {
    post(id: ID!): Post
    posts: [Post]
  }

  type Post {
    id: ID
    title: String
    content: String
  }
`);

const root = {
  post: async ({ id }) => {
    return await getPostById(id);
  },
  posts: async () => {
    return await getAllPosts();
  }
};

const app = express();
app.use('/graphql', graphqlHTTP({
  schema: schema,
  rootValue: root,
  graphiql: true,
}));

initDB().then(() => {
  app.listen(4000, () => console.log('Serving from localhost:4000/graphql'));
}).catch(err => {
  console.error('Failed to initialize the database:', err);
});
