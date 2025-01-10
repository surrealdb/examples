import { RecordId } from "surrealdb";

export type PollVote = {
	id: RecordId<"pollVote">;
	in: RecordId<"user">;
	out: RecordId<"">;
};