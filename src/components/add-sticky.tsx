'use client';

import { useCreateStickyStore } from '@/lib/state';
import { StickyColor, style } from '@/lib/style';
import { cn } from '@/lib/utils';
import { Plus } from 'lucide-react';
import React from 'react';

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
