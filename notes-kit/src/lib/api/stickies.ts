import { record } from "$lib/zod";
import { Sticky, StickyColor } from "$schema/sticky";
import { StringRecordId, jsonify } from "surrealdb";
import { z } from "zod";
import { getDb } from "../surreal";

export async function fetchStickies() {
	const db = await getDb();
	const result = await db.select<Sticky>("sticky");
	return z.array(Sticky).parse(jsonify(result));
}

export async function fetchSticky(id: Sticky["id"]) {
	const recordId = new StringRecordId(record("sticky").parse(id));
	const db = await getDb();
	const result = await db.select<Sticky>(recordId);
	return await Sticky.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function createSticky({
	color,
	content,
}: Pick<Sticky, "color" | "content">) {
	color = StickyColor.parse(color);
	content = z.string().parse(content);

	const db = await getDb();
	const [result] = await db.create<Sticky, Pick<Sticky, "color" | "content">>(
		"sticky",
		{
			color,
			content,
		},
	);

	return await Sticky.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function updateSticky(
	id: Sticky["id"],
	{ color, content }: Partial<Pick<Sticky, "color" | "content">>,
) {
	const recordId = new StringRecordId(record("sticky").parse(id));
	color = StickyColor.optional().parse(color);
	content = z.string().optional().parse(content);

	const db = await getDb();
	const result = await db.merge<
		Sticky,
		Partial<Pick<Sticky, "color" | "content">>
	>(recordId, {
		color,
		content,
	});

	return await Sticky.parseAsync(jsonify(result)).catch(() => undefined);
}

export async function deleteSticky(id: Sticky["id"]) {
	const recordId = new StringRecordId(record("sticky").parse(id));
	const db = await getDb();
	const result = await db.delete<Sticky>(recordId);
	return await Sticky.parseAsync(jsonify(result)).catch(() => undefined);
}
