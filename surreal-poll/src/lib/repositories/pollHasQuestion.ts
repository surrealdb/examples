import Surreal, { RecordId, StringRecordId } from "surrealdb";
import { Poll } from "~/types/poll";
import { PollHasQuestion } from "~/types/pollHasQuestion";

export async function relatePollToQuestions(
	db: Surreal,
	poll: Poll,
	questions: RecordId<"pollQuestion">[]
): Promise<PollHasQuestion[]> {
	const id = new StringRecordId(poll.id);
	return await db.relate(id, "pollHasQuestion", questions) as PollHasQuestion[];
}