import { getDb, initDb } from "../utils/surreal";

export async function getAllUsers() {
    const db = await initDb();
    if (!db) {
        console.error("Database not initialized");
        return;
    }
    try {
        const users = await db.select('User');
        console.log("All users:", users);
    } catch (err) {
        console.error("Failed to get users:", err);
    }
}

getAllUsers();