import { RecordId } from "surrealdb";

export interface UserRecord {
	id: RecordId<"user">;
	name: string;
	email: string;
	pass: string;
}