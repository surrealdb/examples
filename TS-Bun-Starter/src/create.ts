import { getDb, initDb } from "../utils/surreal";

async function createUser() {
    const db = await initDb();
    if (!db) {
        console.error("Database not initialized");
        return;
    }
    try {
        const user = await db.create('User', {
            // User details
            username: "newUser",
            email: "user@example.com",
            password: "securePassword", // Note: Store hashed passwords, not plain text
        });
        console.log("User created:", user);
    } catch (err) {
        console.error("Failed to create user:", err);
    }
}

createUser();