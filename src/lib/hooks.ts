'use client';

import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import {
    createSticky,
    deleteSticky,
    fetchStickies,
    fetchSticky,
    updateSticky,
} from './modifiers';
import { useStickiesStore } from './stores';

export const useStickies = () => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWR('/api/sticky', async () => {
        const res = await fetchStickies();
        merge(res.stickies);
        return res;
    });
};

export const useSticky = (id: string) => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWR(`/api/sticky`, async () => {
        const res = await fetchSticky(id);
        if (res.sticky) merge([res.sticky]);
        return res;
    });
};

export const useCreateSticky = () => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWRMutation(
        `/api/sticky`,
        async (_, { arg }: { arg: Parameters<typeof createSticky>[0] }) => {
            const res = await createSticky(arg);
            if (res.sticky) merge([res.sticky]);
            return res;
        }
    );
};

export const useUpdateSticky = (id: string) => {
    const merge = useStickiesStore((s) => s.mergeStickies);
    return useSWRMutation(
        `/api/sticky`,
        async (_, { arg }: { arg: Parameters<typeof updateSticky>[1] }) => {
            const res = await updateSticky(id, arg);
            if (res.sticky) merge([res.sticky]);
            return res;
        }
    );
};

export const useDeleteSticky = (id: string) => {
    const deleteStickyFromStore = useStickiesStore((s) => s.deleteSticky);
    return useSWRMutation(`/api/sticky`, async () => {
        const res = await deleteSticky(id);
        if (res.sticky) deleteStickyFromStore(res.sticky.id);
        return res;
    });
};
