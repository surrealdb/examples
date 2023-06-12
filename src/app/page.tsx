'use client';

import { Sticky } from '@/components/sticky';
import { useStickies } from '@/lib/hooks';
import { Loader2 } from 'lucide-react';
import React from 'react';

export default function Home() {
    const { data, isLoading } = useStickies();

    const message = data?.stickies.length == 0 ? 'Create a sticky!' : undefined;

    return isLoading ? (
        <div className="flex h-full w-full items-center justify-center">
            <h1 className="flex items-center gap-4 text-2xl">
                <Loader2 className="animate-spin" />
                Loading stickies
            </h1>
        </div>
    ) : message ? (
        <div className="flex h-full w-full items-center justify-center">
            <h1 className="text-2xl">{message}</h1>
        </div>
    ) : (
        <div className="grid w-full grid-cols-1 gap-6 sm:py-16 md:grid-cols-2 xl:grid-cols-3">
            {data?.stickies.map(({ id, content, color }) => (
                <Sticky key={id} id={id} color={color} content={content} />
            ))}
        </div>
    );
}
