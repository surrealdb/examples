import Surreal from 'surrealdb.js';

export const endpoint = 'ws://localhost:3001/rpc';
export const namespace = 'test';
export const database = 'test';

export const surreal = new Surreal(endpoint, {
    prepare: async () => {
        await surreal.use({
            ns: namespace,
            db: database,
        });

        if (typeof localStorage !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token)
                await surreal.authenticate(token).catch((e) => {
                    console.warn(`Failed to authenticate: ${e}`);
                });
        }
    },
});
