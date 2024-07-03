import { Surreal } from "surrealdb.js";

let db: Surreal | undefined;

export async function initDb(): Promise<Surreal | undefined> {
    if (db) return db;
    const surreal = new Surreal();
    try {
        await surreal.connect("http://127.0.0.1:8000/rpc");
        await surreal.use({ namespace: "test", database: "test" });
        // db = surreal;
        return db;
    } catch (err) {
        console.error("Failed to connect to SurrealDB:", err);
        throw err;
    }
}

export async function closeDb(): Promise<void> {
    if (!db) return;
    await db.close();
    db = undefined;
}

export function getDb(): Surreal | undefined {
    return db;
}