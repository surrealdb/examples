import { record } from '@/lib/zod';
import z from 'zod';

export const AssignedTo = z.object({
    id: record('assigned_to'),
    in: record('tag'),
    out: record('sticky'),
    created: z.coerce.date(),
    updated: z.coerce.date(),
});

export type AssignedTo = z.infer<typeof AssignedTo>;
