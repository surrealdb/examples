import { Sticky } from '@/app/api/sticky/lib';
import { create } from 'zustand';

interface StickiesStore {
    editing: string | null;
    setEditing: (id: string | null) => void;

    stickies: Record<string, Sticky>;
    mergeStickies: (updates: Sticky[]) => void;
    deleteSticky: (id: string) => void;
    addSticky: (sticky: Sticky) => void;
}

export const useStickiesStore = create<StickiesStore>((set) => ({
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
}));
