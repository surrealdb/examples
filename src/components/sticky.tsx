'use client';

import { useDeleteSticky, useUpdateSticky } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { X } from 'lucide-react';
import React from 'react';
import { StickyEditor } from './sticky-editor';

const style = cva('', {
    variants: {
        color: {
            purple: 'bg-purple-sticky',
            pink: 'bg-pink-sticky',
        },
    },
});

// Looks more complex than it actually is
// This essentially extracts a type for the colors that we can pass
export type StickyColor = Exclude<
    Exclude<Parameters<typeof style>[0], undefined>['color'],
    null | undefined
>;

export function Sticky({
    id,
    color,
    content,
}: {
    id: string;
    color: StickyColor;
    content: string;
}) {
    const { trigger: deleteSticky } = useDeleteSticky(id);
    const { trigger: updateSticky } = useUpdateSticky(id);

    return (
        <div className="relative transition-transform hover:scale-105">
            <button
                className="absolute right-0 top-0 z-10 m-4 border-none bg-transparent p-0 text-white outline-none"
                onClick={() => deleteSticky()}
            >
                <X size={30} />
            </button>
            <StickyEditor
                title="Edit sticky"
                onSubmit={updateSticky}
                color={color}
                initialValue={content}
            >
                <div
                    className={cn(
                        'relative aspect-square w-full cursor-pointer rounded-4xl px-10 py-14 text-2xl text-dark',
                        style({ color })
                    )}
                >
                    {content}
                </div>
            </StickyEditor>
        </div>
    );
}
