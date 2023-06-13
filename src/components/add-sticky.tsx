'use client';

import { useCreateStickyStore } from '@/lib/state';
import { cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { Plus } from 'lucide-react';
import React from 'react';

export const style = cva('', {
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

export function AddSticky({ color }: { color: StickyColor }) {
    const setCreateColor = useCreateStickyStore((s) => s.setCreateColor);

    return (
        <button
            className={cn(
                'flex h-10 w-10 items-center justify-center rounded-xl border-none text-white outline-none transition-transform hover:scale-110 sm:h-12 sm:w-12',
                style({ color })
            )}
            onClick={() => setCreateColor(color)}
        >
            <Plus />
        </button>
    );
}
