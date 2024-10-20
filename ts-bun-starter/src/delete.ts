import { jsonify } from "surrealdb";
import { getDb } from "../utils/surreal";

export async function deleteUser() {
  const db = await getDb();
  if (!db) {
    console.error("Database not initialized");
    return;
  }
  try {
    const deletedUser = await db.delete('User');
    console.log("Deleted user:", jsonify(deletedUser));
    return deletedUser;
  } catch (err) {
    console.error("Failed to delete user:", err);
  } finally {
    await db.close();
  }
}


deleteUser();