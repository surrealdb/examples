import Surreal, { RecordId, Table } from "surrealdb";
import { Poll, PollPayload } from "~/types/poll";
import { createPollQuestions } from "./pollQuestion";
import { relatePollToQuestions } from "./pollHasQuestion";

export async function createPoll(
	db: Surreal,
	data: PollPayload
): Promise<Poll> {
	const [poll] = await db.create("poll", { title: data.title }) as [Poll];
	const questions = await createPollQuestions(db, data.questions);
	await relatePollToQuestions(db, poll, questions.map((question) => question.id));

	return poll;
}

export async function deletePoll(
	db: Surreal,
	id: RecordId<"poll">
): Promise<Poll> {
	const poll = await db.delete(id);
	return poll as Poll;
}

export async function getPoll(
	db: Surreal,
	id: RecordId<"poll">
): Promise<Poll> {
	const poll = await db.select(id);
	return poll as Poll;
}