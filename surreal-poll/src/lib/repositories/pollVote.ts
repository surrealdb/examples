import Surreal, { RecordId } from "surrealdb";
import { PollVote } from "~/types/pollVote";

export async function votePollQuestion(
	db: Surreal,
	user: RecordId<"user">,
	question: RecordId<"pollQuestion">
): Promise<PollVote> {
	const [vote] = await db.relate(user, "pollVote", question);
	return vote as PollVote;
}