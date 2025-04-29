import Surreal from "surrealdb";
import { Poll } from "~/types/poll";
import { PollQuestion } from "~/types/pollQuestion";

export async function createPollQuestions(
	db: Surreal,
	data: string[]
): Promise<PollQuestion[]> {
	const questions = await db.insert("pollQuestion", data.map((question) => ({ question })));
	return questions as unknown as PollQuestion[];
}

export async function getPollQuestions(
	db: Surreal,
	poll: Poll
): Promise<PollQuestion[]> {

	const [questions] = await db.query(`
		SELECT VALUE ->pollHasQuestion->pollQuestion as questions
		FROM ONLY $id
		FETCH questions
	`, { id: poll.id });

	return questions as PollQuestion[];
}