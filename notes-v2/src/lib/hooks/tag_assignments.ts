import { Sticky } from '@/schema/sticky';
import { Tag } from '@/schema/tag';
import useSWR from 'swr';
import useSWRMutation from 'swr/mutation';
import {
    assignTag,
    assignedTags,
    unassignTag,
} from '../modifiers/tag_assignments';

export const useAssignTag = (sticky: Sticky['id']) => {
    return useSWRMutation(
        `/api/tag/assignment/${sticky}`,
        async (_, { arg: tag }: { arg: Tag['id'] }) => {
            return await assignTag({ sticky, tag });
        }
    );
};

export const useUnassignTag = (sticky: Sticky['id']) => {
    return useSWRMutation(
        `/api/tag/assignment/${sticky}`,
        async (_, { arg: tag }: { arg: Tag['id'] }) => {
            return await unassignTag({ sticky, tag });
        }
    );
};

export const useAssignedTags = (id: Sticky['id']) => {
    return useSWR(`/api/tag/assignment/${id}`, async () => {
        const assigned_tags = await assignedTags(id);
        return assigned_tags;
    });
};
