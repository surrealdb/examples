import z from 'zod';

export function record<Table extends string = string>(table?: Table) {
    return z.custom<`${Table}:${string}`>(
        (val) =>
            typeof val === 'string' && table
                ? val.startsWith(table + ':')
                : true,
        {
            message: ['Must be a record', table && `Table must be: "${table}"`]
                .filter((a) => a)
                .join('; '),
        }
    );
}
