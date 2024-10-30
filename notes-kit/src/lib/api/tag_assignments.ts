import { getDb } from "$lib/surreal";
import { record } from "$lib/zod";
import type { AssignedTo } from "$schema/assigned_to";
import type { Sticky } from "$schema/sticky";
import { Tag } from "$schema/tag";
import { StringRecordId, jsonify } from "surrealdb";
import { z } from "zod";

export async function assignTag({
	tag,
	sticky,
}: {
	tag: Tag["id"];
	sticky: Sticky["id"];
}) {
	const tagRecordId = new StringRecordId(record("tag").parse(tag));
	const stickyRecordId = new StringRecordId(record("sticky").parse(sticky));

	const db = await getDb();
	const [result] = await db.query<[AssignedTo[]]>(
		/* surrealql */ `
            RELATE ONLY $tag->assigned_to->$sticky;
        `,
		{ tag: tagRecordId, sticky: stickyRecordId },
	);

	return !!result && result.length > 0;
}

export async function unassignTag({
	tag,
	sticky,
}: {
	tag: Tag["id"];
	sticky: Sticky["id"];
}) {
	const tagRecordId = new StringRecordId(record("tag").parse(tag));
	const stickyRecordId = new StringRecordId(record("sticky").parse(sticky));

	const db = await getDb();
	const [result] = await db.query<[AssignedTo[]]>(
		/* surrealql */ `
            DELETE $tag->assigned_to WHERE out = $sticky RETURN BEFORE;
        `,
		{ tag: tagRecordId, sticky: stickyRecordId },
	);

	return !!result && result.length > 0;
}

export async function loadAssignedTags(sticky: Sticky["id"]) {
	const stickyRecordId = new StringRecordId(record("sticky").parse(sticky));

	const db = await getDb();
	const [result] = await db.query<[Tag[]]>(
		/* surrealql */ `
            $sticky<-assigned_to<-tag.*
        `,
		{ sticky: stickyRecordId },
	);

	return z
		.array(Tag)
		.parse(jsonify(result) ?? [])
		.filter(
			({ id }, index, arr) => index === arr.findIndex((item) => item.id === id),
		);
}
