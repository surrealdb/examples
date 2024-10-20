
import { getDb } from "../utils/surreal";
import { jsonify } from "surrealdb";

interface User {
  id: string;
  // Add other user properties here
}

export async function getAllUsers(): Promise<User[] | undefined> {
  const db = await getDb();
  if (!db) {
    console.error("Database not initialized");
    return undefined;
  }
  try {
    const users = await db.select<User>("User");
    console.log("All users:", jsonify(users));
    return users;
  } catch (err) {
    console.error("Failed to get users:", err);
    return undefined;
  } finally {
    await db.close();
  }
}

// Remove this line if you don't want to immediately call the function
getAllUsers();