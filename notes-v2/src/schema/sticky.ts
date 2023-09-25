import { record } from '@/lib/zod';
import z from 'zod';

export const StickyColor = z.union([z.literal('pink'), z.literal('purple')]);
export type StickyColor = z.infer<typeof StickyColor>;

export const Sticky = z.object({
    id: record('sticky'),
    content: z.string(),
    color: StickyColor,
    author: record('user'),
    created: z.coerce.date(),
    updated: z.coerce.date(),
});

export type Sticky = z.infer<typeof Sticky>;
