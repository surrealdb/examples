import { createSignal, For, type Component } from 'solid-js';
import { createStore } from 'solid-js/store';
import { Button } from '~/components/ui/button';
import { TextField, TextFieldInput, TextFieldLabel } from '~/components/ui/text-field';
import { showToast } from '~/components/ui/toast';
import { useSurreal } from '~/lib/providers/surrealdb';
import { createPoll } from '~/lib/repositories/poll';

interface CreatePollStore {
	title: string;
	questions: string[];
}

const CreatePoll: Component = () => {

	const { client } = useSurreal();

	const [store, setStore] = createStore<CreatePollStore>({
		title: "",
		questions: []
	});

	const createPollMutation = async () => {
		const db = client();
		await createPoll(db, { title: store.title, questions: store.questions });

		showToast({
			title: "Poll Created",
			description: "Your poll has been created successfully.",
		});
	};

	const addQuestion = () => {
		setStore("questions", [...store.questions, ""]);
	};

	const updateQuestion = (index: number, value: string) => {
		setStore("questions", index, value);
	};

	const deleteQuestion = (index: number) => {
		setStore("questions", store.questions.filter((_, i) => i !== index));
	};

	const updateTitle = (value: string) => {
		setStore("title", value);
	};

	return (
		<div class="container mx-auto p-4">
			<h1 class="text-2xl font-bold mb-4">Create New Poll</h1>
			{/* Add poll creation form here */}
			<TextField>
				<TextFieldLabel>Title</TextFieldLabel>
				<TextFieldInput value={store.title} onChange={(e) => updateTitle(e.target.value)} />
			</TextField>
			<Button onClick={addQuestion}>Add Question</Button>
			<For each={store.questions}>
				{(question, index) => (
					<TextField>
						<TextFieldLabel>Question {index() + 1}</TextFieldLabel>
						<TextFieldInput value={question} onChange={(e) => updateQuestion(index(), e.target.value)} />
						<Button onClick={() => deleteQuestion(index())}>Delete</Button>
					</TextField>
				)}
			</For>
			<Button onClick={createPollMutation}>Create Poll</Button>
		</div>
	);
};

export default CreatePoll;