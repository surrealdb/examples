'use client';

import { Tag } from '@/schema/tag';
import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import {
    createTag,
    deleteTag,
    fetchTag,
    fetchTags,
    updateTag,
} from '../modifiers/tags';

export const useTags = () => useSWR('/api/tag', async () => fetchTags());

export const useTag = (id: Tag['id']) =>
    useSWR(`/api/tag`, async () => fetchTag(id));

export const useCreateTag = () =>
    useSWRMutation(
        `/api/tag`,
        async (_, { arg }: { arg: Parameters<typeof createTag>[0] }) =>
            createTag(arg)
    );

export const useUpdateTag = (id: Tag['id']) =>
    useSWRMutation(
        `/api/tag`,
        async (_, { arg }: { arg: Parameters<typeof updateTag>[1] }) =>
            updateTag(id, arg)
    );

export const useDeleteTag = (id: Tag['id']) =>
    useSWRMutation(`/api/tag`, async () => deleteTag(id));
