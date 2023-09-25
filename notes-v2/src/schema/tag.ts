import { record } from '@/lib/zod';
import z from 'zod';

export const Tag = z.object({
    id: record('tag'),
    name: z.string(),
    owner: record('user'),
    created: z.coerce.date(),
    updated: z.coerce.date(),
});

export type Tag = z.infer<typeof Tag>;
