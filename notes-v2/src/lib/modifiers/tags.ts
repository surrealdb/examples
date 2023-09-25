'use client';

import { Tag } from '@/schema/tag';
import { z } from 'zod';
import { surreal } from '../surreal';
import { record } from '../zod';

export async function fetchTags() {
    const result = await surreal.select<Tag>('tag');
    return z.array(Tag).parse(result);
}

export async function fetchTag(id: Tag['id']) {
    id = record('tag').parse(id);
    const [result] = await surreal.select<Tag>(id);
    return await Tag.parseAsync(result).catch(() => undefined);
}

export async function createTag({ name }: Pick<Tag, 'name'>) {
    name = z.string().parse(name);

    const [result] = await surreal.create<Tag, Pick<Tag, 'name'>>('tag', {
        name,
    });

    return await Tag.parseAsync(result).catch(() => undefined);
}

export async function updateTag(
    id: Tag['id'],
    { name }: Partial<Pick<Tag, 'name'>>
) {
    id = record('tag').parse(id);
    name = z.string().optional().parse(name);

    const [result] = await surreal.merge<Tag, Partial<Pick<Tag, 'name'>>>(id, {
        name,
    });

    return await Tag.parseAsync(result).catch(() => undefined);
}

export async function deleteTag(id: Tag['id']) {
    id = record('tag').parse(id);
    const [result] = await surreal.delete<Tag>(id);
    return await Tag.parseAsync(result).catch(() => undefined);
}
