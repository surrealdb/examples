import { getDb } from "../utils/surreal";
import { jsonify, RecordId } from "surrealdb";

// Type definition (you may want to move this to a separate types file)
interface User {
    id: RecordId;
    username: string;
    password: string;
    email: string;
}

export async function updateUser() {
  const db = await getDb();
  if (!db) {
    console.error("Database not initialized");
    return;
  }
  try {
    const updatedUser = await db.update(new RecordId("User", "6n05gxwudius9ri7mypq"), {
        username: "John Doe",
        email: "john@example.com",
    });
    console.log("Updated user:", jsonify(updatedUser));
    return updatedUser;
  } catch (err) {
    console.error("Failed to update user:", err);
  } finally {
    await db.close();
  }
}

// Example usage:
// updateUser("123", { name: "John Doe", email: "john@example.com" });

updateUser();

