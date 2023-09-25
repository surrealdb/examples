import { Sticky } from '@/schema/sticky';
import { create } from 'zustand';
import { surreal } from '../surreal';

interface StickiesStore {
    editing: string | null;
    setEditing: (id: Sticky['id'] | null) => void;

    stickies: Record<string, Sticky>;
    mergeStickies: (updates: Sticky[]) => void;
    deleteSticky: (id: Sticky['id']) => void;
    addSticky: (sticky: Sticky) => void;

    reset: () => void;
}

export const useStickiesStore = create<StickiesStore>((set) => {
    const store = {
        editing: null,
        setEditing: (id) => set(() => ({ editing: id })),

        stickies: {},
        mergeStickies: (updates) =>
            set(({ stickies }) => ({
                stickies: updates.reduce(
                    (prev, curr) => ({
                        ...prev,
                        [curr.id]: curr,
                    }),
                    stickies
                ),
            })),
        deleteSticky: (id) =>
            set(({ stickies }) => {
                if (id in stickies) delete stickies[id];
                return stickies;
            }),
        addSticky: (sticky) =>
            set(({ stickies }) => ({
                editing: sticky.id,
                stickies: {
                    ...stickies,
                    [sticky.id]: sticky,
                },
            })),
        reset: () =>
            set(() => ({
                editing: null,
                stickies: {},
            })),
    } satisfies StickiesStore;

    surreal.live<Sticky>('sticky', ({ action, result }) => {
        switch (action) {
            case 'CREATE':
            case 'UPDATE':
                store.mergeStickies([Sticky.parse(result)]);
                break;
            case 'DELETE':
                store.deleteSticky(result.id);
                break;
        }
    });

    return store;
});
