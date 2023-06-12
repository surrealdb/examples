'use client';

import { cva } from 'class-variance-authority';
import { X } from 'lucide-react';
import { ReactNode } from 'react';

const style = cva('w-full aspect-square px-8 py-10 rounded-4xl text-dark text-2xl relative', {
    variants: {
        color: {
            purple: 'bg-purple-sticky',
            pink: 'bg-pink-sticky'
        }
    }
});

export type StickyColor = Exclude<
    Exclude<Parameters<typeof style>[0], undefined>['color'],
    null | undefined
>;

export function Sticky({ color, children }: {
    color: StickyColor;
    children: ReactNode;
}) {
    return (
        <div className={style({ color })}>
            <button className="p-0 outline-none border-none bg-transparent text-white absolute top-0 right-0 m-4">
              <X size={32} />
            </button>
            {children}
        </div>
    );
}