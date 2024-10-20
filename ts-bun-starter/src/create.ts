import { getDb } from "../utils/surreal";
import { jsonify } from "surrealdb";

interface User {
  username: string;
  email: string;
  password: string;
}

async function createUser(): Promise<void> {
  const db = await getDb();
  if (!db) {
    console.error("Database not initialized");
    return;
  }
  try {
    const user = await db.create<User>("User", {
      // User details
      username: "newUser",
      email: "user@example.com",
      password: "securePassword", // Note: Store hashed passwords, not plain text
    });
    console.log("User created:", jsonify(user));
  } catch (err: unknown) {
    console.error("Failed to create user:", err instanceof Error ? err.message : String(err));
  } finally {
    await db.close();
  }
}

createUser();