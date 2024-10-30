import { fetchUser } from "$lib/api/user";
import type { User } from "$schema/user";
import { derived, writable } from "svelte/store";

type AuthState = {
	initialized: boolean;
	authenticated: boolean;
	user: undefined | User;
};

const state = writable<AuthState>({
	initialized: false,
	authenticated: false,
	user: undefined,
});

export const refreshAuth = async () => {
	const user = await fetchUser().catch(() => undefined);

	const result = {
		user,
		authenticated: !!user,
	};

	state.set({
		initialized: true,
		...result,
	});

	return result;
};

export const initialized = derived(state, ($state) => $state.initialized);
export const authenticated = derived(state, ($state) => $state.authenticated);
export const user = derived(state, ($state) => $state.user);
export const username = derived(user, ($user) => $user?.username);
