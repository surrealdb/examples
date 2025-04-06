import Surreal from 'surrealdb.js';

let db: Surreal | undefined;

export async function initDb(): Promise<Surreal | undefined> {
    if (db) return db;
    db = new Surreal();
    try {
        await db.connect("http://127.0.0.1:8000/rpc");
        await db.use({ namespace: "test", database: "test" });
        await db.signin({ username: 'root', password: 'root' })

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

        return db;
    } catch (err) {
        console.error("Failed to connect to SurrealDB:", err);
        throw err;
    }
}

interface Post {
  id: string;
  title: string;
  content: string;
}

export const getAllPosts = async (): Promise<Post[]> => {
    const posts = await db?.select('post');
    if (!posts) {
        throw new Error("Failed to fetch posts");
    }
    return posts.map(post => ({
        id: post.id as unknown as string,
        title: post.title as string,
        content: post.content as string,
    })) as Post[];
};
