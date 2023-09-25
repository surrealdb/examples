import { AssignedTo } from '@/schema/assigned_to';
import { Sticky } from '@/schema/sticky';
import { Tag } from '@/schema/tag';
import { z } from 'zod';
import { surreal } from '../surreal';
import { record } from '../zod';

export async function assignTag({
    tag,
    sticky,
}: {
    tag: Tag['id'];
    sticky: Sticky['id'];
}) {
    tag = record('tag').parse(tag);
    sticky = record('sticky').parse(sticky);

    const [result] = await surreal.query<[AssignedTo[]]>(
        /* surrealql */ `
            RELATE ONLY $tag->assigned_to->$sticky;
        `,
        { tag, sticky }
    );

    return result.result && result.result.length > 0;
}

export async function unassignTag({
    tag,
    sticky,
}: {
    tag: Tag['id'];
    sticky: Sticky['id'];
}) {
    tag = record('tag').parse(tag);
    sticky = record('sticky').parse(sticky);

    const [result] = await surreal.query<[AssignedTo[]]>(
        /* surrealql */ `
            DELETE $tag->assigned_to WHERE out = $sticky RETURN BEFORE;
        `,
        { tag, sticky }
    );

    return result.result && result.result.length > 0;
}

export async function assignedTags(sticky: Sticky['id']) {
    sticky = record('sticky').parse(sticky);

    const [result] = await surreal.query<[Tag[]]>(
        /* surrealql */ `
            $sticky<-assigned_to<-tag.*
        `,
        { sticky }
    );

    return z
        .array(Tag)
        .parse(result.result ?? [])
        .filter(
            ({ id }, index, arr) =>
                index == arr.findIndex((item) => item.id == id)
        );
}
