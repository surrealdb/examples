'use client';

import { Sticky, StickyColor } from '@/schema/sticky';
import { z } from 'zod';
import { surreal } from '../surreal';
import { record } from '../zod';

export async function fetchStickies() {
    const result = await surreal.select<Sticky>('sticky');
    return z.array(Sticky).parse(result);
}

export async function fetchSticky(id: Sticky['id']) {
    id = record('sticky').parse(id);
    const [result] = await surreal.select<Sticky>(id);
    return await Sticky.parseAsync(result).catch(() => undefined);
}

export async function createSticky({
    color,
    content,
}: Pick<Sticky, 'color' | 'content'>) {
    color = StickyColor.parse(color);
    content = z.string().parse(content);

    const [result] = await surreal.create<
        Sticky,
        Pick<Sticky, 'color' | 'content'>
    >('sticky', {
        color,
        content,
    });

    return await Sticky.parseAsync(result).catch(() => undefined);
}

export async function updateSticky(
    id: Sticky['id'],
    { color, content }: Partial<Pick<Sticky, 'color' | 'content'>>
) {
    id = record('sticky').parse(id);
    color = StickyColor.optional().parse(color);
    content = z.string().optional().parse(content);

    const [result] = await surreal.merge<
        Sticky,
        Partial<Pick<Sticky, 'color' | 'content'>>
    >(id, {
        color,
        content,
    });

    return await Sticky.parseAsync(result).catch(() => undefined);
}

export async function deleteSticky(id: Sticky['id']) {
    id = record('sticky').parse(id);
    const [result] = await surreal.delete<Sticky>(id);
    return await Sticky.parseAsync(result).catch(() => undefined);
}
