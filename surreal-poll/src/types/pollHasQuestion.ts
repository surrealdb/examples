import { RecordId } from "surrealdb";

export type PollHasQuestion = {
	id: RecordId<"pollHasQuestion">;
	in: RecordId<"poll">;
	out: RecordId<"pollQuestion">;
};