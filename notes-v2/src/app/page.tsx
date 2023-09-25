'use client';

import { Sticky } from '@/components/sticky';
import { useStickies } from '@/lib/hooks/stickies';
import { useAuth } from '@/lib/stores/auth';
import { useStickiesStore } from '@/lib/stores/stickies';
import { Loader2 } from 'lucide-react';
import React from 'react';
import Signin from './auth/signin';
import Signup from './auth/signup';

export default function Home() {
    // Used purely for loading state and automatic refetching.
    // The actual stickies are delivered through the stickies store for far local updates when the user makes a change.
    const { error, isLoading } = useStickies();
    const { stickies } = useStickiesStore();
    const { authenticated, initialized } = useAuth();

    // useEffect(() => {
    //     if (initialized && !authenticated) router.push('/signin');
    // }, [initialized, authenticated, router, user]);

    const sorted = Object.values(stickies).sort(
        (a, b) => b.updated.getTime() - a.updated.getTime()
    );

    const message =
        sorted.length == 0 && initialized && authenticated ? (
            'Create a sticky!'
        ) : error ? (
            <span className="text-red-500">
                <b>An error occured:</b> {error}
            </span>
        ) : undefined;

    return isLoading ? (
        <div className="flex h-full w-full items-center justify-center">
            <h1 className="flex items-center gap-4 text-2xl">
                <Loader2 className="animate-spin" />
                Loading
            </h1>
        </div>
    ) : message ? (
        <div className="flex h-full w-full items-center justify-center">
            <h1 className="text-2xl">{message}</h1>
        </div>
    ) : initialized && !authenticated ? (
        <div className="w-full sm:py-16 md:columns-2 xl:columns-3">
            <Signin />
            <Signup />
        </div>
    ) : (
        <div className="w-full sm:py-16 md:columns-2 xl:columns-3">
            {sorted.map(({ id, content, color }) => (
                <Sticky key={id} id={id} color={color} content={content} />
            ))}
        </div>
    );
}
