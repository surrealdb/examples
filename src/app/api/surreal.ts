import { Surreal } from "surrealdb.js";

export const endpoint = process.env.DB_ENDPOINT ?? 'ws://127.0.0.1:3001/rpc';
export const user = process.env.DB_USER ?? 'root';
export const pass = process.env.DB_PASS ?? 'surrealdb';
export const ns = process.env.DB_NS ?? 'surrealdb-stickies';
export const db = process.env.DB_DB ?? 'surrealdb-stickies';
export const surreal = new Surreal(endpoint, {
    ns,
    db,
    auth: { user, pass }
});