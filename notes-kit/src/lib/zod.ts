import z from "zod";

// export const RecordIdSchema = z.custom<RecordId>(
// 	(value) => value instanceof RecordId,
// 	"Value is not a valid RecordId",
// 	true,
// );

// export function RecordIdSchemaOf<Tb extends string>(table: Tb) {
// 	z.string().parse(table);

// 	return z.custom<RecordId<Tb>>(
// 		(value) => value instanceof RecordId && value.tb === table,
// 		`Value is not a valid RecordId or is not from table: ${table}`,
// 		true,
// 	);
// }

export function record<Table extends string = string>(table?: Table) {
	return z.custom<`${Table}:${string}`>(
		(val) =>
			typeof val === "string" && table ? val.startsWith(`${table}:`) : true,
		{
			message: ["Must be a record", table && `Table must be: "${table}"`]
				.filter((a) => a)
				.join("; "),
		},
	);
}
