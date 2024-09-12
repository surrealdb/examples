import { getDb } from "../utils/surreal";
import { jsonify } from "surrealdb.js";

export async function getAllUsers() {
  const db = await getDb();
  if (!db) {
    console.error("Database not initialized");
    return;
  }
  try {
    const users = await db.select("User");
    console.log("All users:", jsonify(users));
  } catch (err) {
    console.error("Failed to get users:", err);
  } finally {
    await db.close();
  }
}

getAllUsers();
