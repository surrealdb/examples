'use client';

import { useAuth } from '@/lib/stores/auth';
import { surreal } from '@/lib/surreal';
import Image from 'next/image';
import React from 'react';
import useSWRMutation from 'swr/mutation';
import Logo from '../../public/logo.svg';
import { AddSticky } from './add-sticky';

export function Navbar() {
    const { authenticated, refresh, user } = useAuth();

    const { trigger: signout } = useSWRMutation('auth:signout', async () => {
        await surreal.invalidate();
        localStorage.removeItem('token');
        await refresh();
    });

    return (
        <div className="flex justify-between gap-8 py-20 max-md:flex-col max-md:items-center sm:gap-16">
            <Image
                className="max-h-16 w-[auto]"
                src={Logo}
                alt="SurrealDB Stickies logo"
            />

            {authenticated && (
                <div className="flex items-center gap-4">
                    <button onClick={() => signout()}>
                        signout ({user?.username})
                    </button>
                    <AddSticky color="pink" />
                    <AddSticky color="purple" />
                </div>
            )}
        </div>
    );
}
