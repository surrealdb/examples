'use client';

import { User } from '@/schema/user';
import { useEffect, useState } from 'react';
import { create } from 'zustand';
import { surreal } from '../surreal';

export type AuthState = {
    initialized: boolean;
    authenticated: boolean;
    user: null | User;
    refresh: () => Promise<Pick<AuthState, 'authenticated' | 'user'>>;
};

export const useAuth = create<AuthState>((set) => ({
    initialized: false,
    authenticated: false,
    user: null,
    async refresh() {
        const [{ result: info }] = await surreal.query('$auth.*');
        const user = await User.parseAsync(info).catch(() => null);

        const result = {
            user,
            authenticated: !!user,
        };

        set({
            initialized: true,
            ...result,
        });

        return result;
    },
}));

export const InitAuth = () => {
    const [done, setDone] = useState<boolean>(false);
    const { refresh } = useAuth();

    useEffect(() => {
        if (!done) {
            setDone(true);
            refresh();
        }
    }, [setDone, done, refresh]);

    return null;
};
