import { User } from "$schema/user";
import { jsonify } from "surrealdb";
import { getDb } from "../surreal";

export const fetchUser = async () => {
	const db = await getDb();
	const info = await db.info();
	const user = await User.parseAsync(jsonify(info)).catch(() => undefined);
	return user;
};
