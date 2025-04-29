import { PollQuestion } from "~/types/pollQuestion";

interface PollQuestionRowProps {
	question: PollQuestion;
	onVote: (question: PollQuestion) => void;
}

export function PollQuestionRow(props: PollQuestionRowProps) {

	return (
		<div onClick={() => props.onVote(props.question)} class="p-4 border border-gray-200 rounded-md cursor-pointer hover:bg-gray-100">
			<p>{props.question.question}</p>
		</div>
	);
}