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

export const useStickies = () => useSWR('/api/sticky', fetchStickies);
export const useSticky = (id: string) =>
    useSWR(`/api/sticky`, () => fetchSticky(id));

export const useCreateSticky = () =>
    useSWRMutation(
        `/api/sticky`,
        (_, { arg }: { arg: Parameters<typeof createSticky>[0] }) =>
            createSticky(arg)
    );

export const useUpdateSticky = (id: string) =>
    useSWRMutation(
        `/api/sticky`,
        (_, { arg }: { arg: Parameters<typeof updateSticky>[1] }) =>
            updateSticky(id, arg)
    );

export const useDeleteSticky = (id: string) =>
    useSWRMutation(`/api/sticky`, () => deleteSticky(id));
