'use client';

import { useCreateSticky } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { Plus } from 'lucide-react';
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

export type StickyColor = Exclude<
    Exclude<Parameters<typeof style>[0], undefined>['color'],
    null | undefined
>;

export function AddSticky({ color }: { color: StickyColor }) {
    const { trigger: createSticky } = useCreateSticky();

    return (
        <StickyEditor title="Add sticky" color={color} onSubmit={createSticky}>
            <button
                className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-xl border-none text-white outline-none transition-transform hover:scale-110 sm:h-12 sm:w-12',
                    style({ color })
                )}
            >
                <Plus />
            </button>
        </StickyEditor>
    );
}
