import {
	createSticky,
	deleteSticky as deleteStickyAsync,
	fetchStickies,
	updateSticky,
} from "$lib/api/stickies";
import { getDb } from "$lib/surreal";
import { Sticky, type StickyColor } from "$schema/sticky";
import { type Surreal, type Uuid, jsonify } from "surrealdb";
import { derived, writable } from "svelte/store";
import { user } from "./auth.store";

type StickiesState = {
	editing: Sticky["id"] | null;
	stickies: Record<Sticky["id"], Sticky>;
};

const DEFAULT_STATE: StickiesState = {
	editing: null,
	stickies: {},
};

const state = writable<StickiesState>(DEFAULT_STATE);

export const setEditing = (id: Sticky["id"] | null): void => {
	state.update((s) => ({ ...s, editing: id }));
};

const addSticky = (sticky: Sticky): void => {
	state.update(({ stickies }) => ({
		editing: sticky.id,
		stickies: { ...stickies, [sticky.id]: sticky },
	}));
};

const mergeStickies = (updates: Sticky[]): void => {
	state.update((s) => {
		return {
			...s,
			stickies: updates.reduce(
				(prev, curr) => ({
					// biome-ignore lint/performance/noAccumulatingSpread: <explanation>
					...prev,
					[curr.id]: curr,
				}),
				s.stickies,
			),
		};
	});
};

const deleteSticky = (id: Sticky["id"]): void => {
	state.update((s) => {
		if (id in s.stickies) {
			delete s.stickies[id];
		}
		return s;
	});
};

export const resetStickiesState = (): void => {
	state.set(DEFAULT_STATE);
};

export const loadStickies = async () => {
	const response = await fetchStickies();
	mergeStickies(response);
	return response;
};

export const createNewSticky = async (color: StickyColor) => {
	const sticky = await createSticky({
		color,
		content: "",
	});

	if (sticky) {
		addSticky(sticky);
	}
};

export const updateExistingSticky = async (
	id: Sticky["id"],
	{ color, content }: Partial<Pick<Sticky, "color" | "content">>,
) => {
	const sticky = await updateSticky(id, { color, content });

	if (sticky) {
		mergeStickies([sticky]);
		setEditing(null);
	}
};

export const deleteExistingSticky = async (id: Sticky["id"]) => {
	const sticky = await deleteStickyAsync(id);

	if (sticky) {
		deleteSticky(id);
		setEditing(null);
	}
};

export const editing = derived(state, ($state) => $state.editing);
const stickies = derived(state, ($state) => $state.stickies);

export const sortedStickies = derived(stickies, ($stickies) => {
	return Object.values($stickies).sort(
		(a, b) => b.updated.getTime() - a.updated.getTime(),
	);
});

// listen to live query updates
user.subscribe(async (user) => {
	let queryUuid: Uuid | undefined;
	let db: Surreal | undefined;

	if (user) {
		try {
			db = await getDb();
			queryUuid = await db.live<Sticky>("sticky", (action, result) => {
				switch (action) {
					case "CREATE":
					case "UPDATE":
						mergeStickies([Sticky.parse(jsonify(result))]);
						break;
					case "DELETE":
						deleteSticky(jsonify(result.id));
						break;
				}
			});
		} catch (err) {
			console.error(
				"Failed to create live query:",
				err instanceof Error ? err.message : String(err),
			);
		}
	}

	return async () => {
		if (db && queryUuid) {
			await db.kill(queryUuid);
		}
	};
});
