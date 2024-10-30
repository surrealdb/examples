import { record } from "$lib/zod";
import z from "zod";

export const User = z.object({
	id: record("user"),
	name: z.string(),
	username: z.string().toLowerCase(),
	created: z.coerce.date(),
	updated: z.coerce.date(),
});

export type User = z.infer<typeof User>;
