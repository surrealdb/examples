import { RecordId } from "surrealdb";

export interface PollQuestion {
	id: RecordId<"pollQuestion">;
	question: string;
}