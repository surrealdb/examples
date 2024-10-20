
import Surreal from "surrealdb";

interface DbConfig {
  url: string;
  namespace: string;
  database: string;
}

const DEFAULT_CONFIG: DbConfig = {
  url: "http://127.0.0.1:8000/rpc",
  namespace: "test",
  database: "test",
};

export async function getDb(config: DbConfig = DEFAULT_CONFIG): Promise<Surreal> {
  const db = new Surreal();

  try {
    await db.connect(config.url);
    await db.use({ namespace: config.namespace, database: config.database });
    return db;
  } catch (err) {
    console.error("Failed to connect to SurrealDB:", err instanceof Error ? err.message : String(err));
    await db.close();
    throw err;
  }
}