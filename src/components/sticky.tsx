'use client';

import { useDeleteSticky, useUpdateSticky } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { X } from 'lucide-react';
import React, { createRef, useCallback, useEffect, useState } from 'react';
import { Textarea } from './sticky-editor';

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
    const ref = createRef<HTMLDivElement>();
    const [editing, setEditing] = useState(false);
    const { trigger: deleteSticky } = useDeleteSticky(id);
    const { trigger: updateSticky } = useUpdateSticky(id);

    const submit = useCallback(
        (content: string) => {
            updateSticky({ color, content });
            setEditing(false);
        },
        [color, updateSticky]
    );

    useEffect(() => {
        const handler = (event: globalThis.MouseEvent) => {
            if (ref.current && !ref.current.contains(event.target as Node)) {
                setEditing(false);
            }
        };
        window.addEventListener('mousedown', handler);
        return () => window.removeEventListener('mousedown', handler);
    }, [ref]);

    return (
        <div
            className={cn(
                'relative rounded-4xl transition-transform hover:scale-105 hover:shadow-lg active:scale-100',
                editing && 'scale-105 shadow-lg'
            )}
            ref={ref}
        >
            <button
                className="absolute right-0 top-0 z-10 m-4 border-none bg-transparent p-0 text-white outline-none"
                onClick={() => deleteSticky()}
            >
                <X size={30} />
            </button>
            <button
                className={cn(
                    'relative flex aspect-square w-full cursor-pointer flex-col items-start rounded-4xl border-none px-10 py-14 text-left text-2xl text-dark outline-none',
                    style({ color })
                )}
                onClick={() => setEditing(true)}
            >
                {editing ? (
                    <Textarea
                        initialValue={content}
                        onSubmit={submit}
                        editing={editing}
                        setEditing={setEditing}
                    />
                ) : (
                    <p>{content}</p>
                )}
            </button>
        </div>
    );
}
