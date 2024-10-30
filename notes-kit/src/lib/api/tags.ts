import { record } from "$lib/zod";
import { Tag } from "$schema/tag";
import { StringRecordId, jsonify } from "surrealdb";
import { z } from "zod";
import { getDb } from "../surreal";

export async function fetchTags() {
	const db = await getDb();
	const result = await db.select<Tag>("tag");
	return z.array(Tag).parse(jsonify(result));
}

export async function fetchTag(id: Tag["id"]) {
	const db = await getDb();
	const recordId = new StringRecordId(record("tag").parse(id));
	const result = await db.select<Tag>(recordId);
	return await Tag.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function createTag({ name }: Pick<Tag, "name">) {
	name = z.string().parse(name);

	const db = await getDb();
	const [result] = await db.create<Tag, Pick<Tag, "name">>("tag", {
		name,
	});

	return await Tag.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function updateTag(
	id: Tag["id"],
	{ name }: Partial<Pick<Tag, "name">>,
) {
	const recordId = new StringRecordId(record("tag").parse(id));
	name = z.string().optional().parse(name);

	const db = await getDb();
	const result = await db.merge<Tag, Partial<Pick<Tag, "name">>>(recordId, {
		name,
	});

	return await Tag.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function deleteTag(id: Tag["id"]) {
	const recordId = new StringRecordId(record("tag").parse(id));
	const db = await getDb();
	const result = await db.delete<Tag>(recordId);
	return await Tag.parseAsync(jsonify(result)).catch(() => undefined);
}
