import type { Component } from 'solid-js';
import { useParams } from '@solidjs/router';

const PollResults: Component = () => {
	const params = useParams();
	

	return (
		<div class="container mx-auto p-4">
			<h1 class="text-2xl font-bold mb-4">Poll Results</h1>
			<p>Poll ID: {params.id}</p>
			{/* Add results display here */}
		</div>
	);
};

export default PollResults;