import Surreal from "surrealdb";

export async function getDb(): Promise<Surreal | undefined> {
  const db = new Surreal();

  try {
    await db.connect("http://127.0.0.1:8000/rpc");
    await db.use({ namespace: "test", database: "test" });
    return db;
  } catch (err) {
    console.error("Failed to connect to SurrealDB:", err);
    await db.close();
    throw err;
  }
}
