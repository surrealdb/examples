import { derived, writable } from "svelte/store";

export type DialogType = "TagPicker";

type DialogState = {
	openedDialog: DialogType | undefined;
};

const state = writable<DialogState>({
	openedDialog: undefined,
});

export const openDialog = (dialog: DialogType): void => {
	state.update((s) => ({ ...s, openedDialog: dialog }));
};

export const closeDialog = (): void => {
	state.update((s) => ({ ...s, openedDialog: undefined }));
};

const openedDialog = derived(state, ($state) => $state.openedDialog);

export const isTagPickerDialogOpened = derived(
	openedDialog,
	($openedDialog) => $openedDialog === "TagPicker",
);
