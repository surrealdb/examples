import type { Component } from 'solid-js';
import { Router, Route } from "@solidjs/router";
import { SurrealProvider } from './lib/providers/surrealdb';
import { QueryClientProvider } from '@tanstack/solid-query';
import { tanstackClient } from './lib/query-client';
import { Navbar } from './components/Navbar';
import { AuthProvider } from './lib/providers/auth';
import Home from './pages/Home';
import CreatePoll from './pages/CreatePoll';
import VotePoll from './pages/VotePoll';
import PollResults from './pages/PollResults';
import { AppLayout } from './components/layout/app';
import { Signin } from './pages/Signin';
import { Signup } from './pages/Signup';
import { Toaster } from './components/ui/toast';

const App: Component = () => {
	return (
		<QueryClientProvider client={tanstackClient}>
			<SurrealProvider
				endpoint={import.meta.env.VITE_DB_HOST}
				autoConnect
				params={{
					namespace: "surrealdb",
					database: "pollwebapp",
				}}
			>
				<AuthProvider>
					<Router>
						<Route path="/" component={AppLayout}>
							<Route path="/" component={Home} />
							<Route path="/create" component={CreatePoll} />
							<Route path="/poll/:id" component={VotePoll} />
							<Route path="/poll/:id/results" component={PollResults} />
							<Route path="/signin" component={Signin} />
							<Route path="/signup" component={Signup} />
						</Route>
					</Router>
					<Toaster />
				</AuthProvider>
			</SurrealProvider>
		</QueryClientProvider>
	);
};

export default App;
