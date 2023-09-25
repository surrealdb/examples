'use client';

import { Sticky } from '@/schema/sticky';
import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import {
    createSticky,
    deleteSticky,
    fetchStickies,
    fetchSticky,
    updateSticky,
} from '../modifiers/stickies';
import { useStickiesStore } from '../stores/stickies';

export const useStickies = () => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWR('/api/sticky', async () => {
        const stickies = await fetchStickies();
        merge(stickies);
        return stickies;
    });
};

export const useSticky = (id: Sticky['id']) => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWR(`/api/sticky`, async () => {
        const sticky = await fetchSticky(id);
        if (sticky) merge([sticky]);
        return sticky;
    });
};

export const useCreateSticky = () => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWRMutation(
        `/api/sticky`,
        async (_, { arg }: { arg: Parameters<typeof createSticky>[0] }) => {
            const sticky = await createSticky(arg);
            if (sticky) merge([sticky]);
            return sticky;
        }
    );
};

export const useUpdateSticky = (id: Sticky['id']) => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWRMutation(
        `/api/sticky`,
        async (_, { arg }: { arg: Parameters<typeof updateSticky>[1] }) => {
            const sticky = await updateSticky(id, arg);
            if (sticky) merge([sticky]);
            return sticky;
        }
    );
};

export const useDeleteSticky = (id: Sticky['id']) => {
    const deleteStickyFromStore = useStickiesStore((s) => s.deleteSticky);
    return useSWRMutation(`/api/sticky`, async () => {
        const sticky = await deleteSticky(id);
        if (sticky) deleteStickyFromStore(sticky.id);
        return sticky;
    });
};
