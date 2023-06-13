'use client';

import { Sticky, StickyFramework } from '@/components/sticky';
import { useCreateSticky, useStickies } from '@/lib/hooks';
import { useCreateStickyStore } from '@/lib/state';
import { Loader2 } from 'lucide-react';
import React, { useCallback } from 'react';

export default function Home() {
    const { data, error, isLoading } = useStickies();
    const { createColor, setCreateColor } = useCreateStickyStore((s) => s);
    const { trigger: createSticky } = useCreateSticky();

    const submit = useCallback(
        (content: string) => {
            if (createColor) {
                createSticky({ color: createColor, content });
                setCreateColor(null);
            }
        },
        [createColor, createSticky, setCreateColor]
    );

    const message =
        data?.stickies.length == 0 ? (
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
                Loading stickies
            </h1>
        </div>
    ) : message ? (
        <div className="flex h-full w-full items-center justify-center">
            <h1 className="text-2xl">{message}</h1>
        </div>
    ) : (
        <div className="grid w-full grid-cols-1 gap-6 sm:py-16 md:grid-cols-2 xl:grid-cols-3">
            {createColor && (
                <StickyFramework
                    color={createColor}
                    onClose={() => setCreateColor(null)}
                    onDelete={() => setCreateColor(null)}
                    onSubmit={submit}
                    editing={true}
                />
            )}
            {data?.stickies.map(({ id, content, color }) => (
                <Sticky key={id} id={id} color={color} content={content} />
            ))}
        </div>
    );
}
