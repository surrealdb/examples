'use client';

import { useCreateSticky } from '@/lib/hooks/stickies';
import { useStickiesStore } from '@/lib/stores/stickies';
import { CVAProp, cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { Plus } from 'lucide-react';
import React, { useCallback } from 'react';

export const style = cva('', {
    variants: {
        color: {
            purple: 'bg-purple-sticky',
            pink: 'bg-pink-sticky',
        },
    },
});

export type StickyColor = CVAProp<typeof style, 'color'>;

export function AddSticky({ color }: { color: StickyColor }) {
    const { trigger: createSticky } = useCreateSticky();
    const { addSticky } = useStickiesStore();
    const onSubmit = useCallback(async () => {
        const sticky = await createSticky({
            color,
            content: '',
        });

        if (sticky) addSticky(sticky);
    }, [color, createSticky, addSticky]);

    return (
        <button
            className={cn(
                'flex h-10 w-10 items-center justify-center rounded-xl border-none text-white outline-none transition-transform hover:scale-110 sm:h-12 sm:w-12',
                style({ color })
            )}
            onClick={onSubmit}
        >
            <Plus />
        </button>
    );
}
