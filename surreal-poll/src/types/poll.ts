import { RecordId } from "surrealdb";

export type Poll = {
	id: RecordId;
	title: string;
	creator: RecordId<"user">;
}

export type PollPayload = {
	title: string;
	questions: string[];
};