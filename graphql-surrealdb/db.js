import Surreal from 'surrealdb.js';

const db = new Surreal();

const initDB = async () => {
  await db.connect('http://127.0.0.1:8000/rpc');
  await db.use({ namespace: "test", database: "test" });

  await db.query(`
    CREATE post CONTENT {
      title: 'Hello from SurrealDB',
      content: 'This is a hello from SurrealDB'
    };
    CREATE post CONTENT {
      title: 'SurrealDB is Awesome',
      content: 'This is a post about SurrealDB'
    };
  `);
};

const getPostById = async (id) => {
  const post = await db.select(`post:${id}`);
  return post[0];
};

const getAllPosts = async () => {
  return await db.select('post');
};

export { initDB, getPostById, getAllPosts };
