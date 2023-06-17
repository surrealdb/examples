'use client';

import { useDeleteSticky, useUpdateSticky } from '@/lib/hooks';
import { useStickiesStore } from '@/lib/stores';
import { cn } from '@/lib/utils';
import { cva } from 'class-variance-authority';
import { Loader2, X } from 'lucide-react';
import React, {
    KeyboardEvent,
    createRef,
    useCallback,
    useEffect,
    useState,
} from 'react';

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

export function Sticky({
    id,
    color,
    content,
}: {
    id: string;
    color: StickyColor;
    content: string;
}) {
    const [loading, setLoading] = useState(false);
    const { trigger: deleteSticky } = useDeleteSticky(id);
    const { trigger: updateSticky } = useUpdateSticky(id);
    const {
        deleteSticky: deleteStickyFromCache,
        mergeStickies,
        editing,
        setEditing,
    } = useStickiesStore();

    const submit = useCallback(
        async (content?: string) => {
            if (typeof content == 'string') {
                setLoading(true);
                const res = await updateSticky({ color, content });
                if (res?.sticky) mergeStickies([res.sticky]);
            }

            setEditing(null);
            setLoading(false);
        },
        [color, updateSticky, mergeStickies, setEditing]
    );

    const onDelete = useCallback(async () => {
        const res = await deleteSticky();
        if (res?.sticky) deleteStickyFromCache(res.sticky.id);
        setEditing(null);
    }, [deleteSticky, deleteStickyFromCache, setEditing]);

    return (
        <StickyFramework
            color={color}
            content={content}
            onClick={() => setEditing(id)}
            onClose={submit}
            onDelete={onDelete}
            editing={editing === id}
            loading={loading}
        />
    );
}

export function StickyFramework({
    color,
    content,
    onClick,
    onClose,
    onDelete,
    editing,
    loading,
}: {
    color: StickyColor;
    content?: string;
    onClick?: () => unknown;
    onClose?: (content?: string) => unknown;
    onDelete?: () => unknown;
    editing?: boolean;
    loading?: boolean;
}) {
    const containerRef = createRef<HTMLDivElement>();
    const textareaRef = createRef<HTMLTextAreaElement>();

    const textAreaAdjust = useCallback(() => {
        const self = textareaRef.current;
        if (self)
            setTimeout(function () {
                self.style.cssText = 'height:auto; padding:0';
                self.style.cssText = 'height:' + self.scrollHeight + 'px';
            }, 0);
    }, [textareaRef]);

    const close = useCallback(() => {
        if (editing) {
            const value = textareaRef.current?.value?.trim() ?? '';
            onClose?.(value === content ? undefined : value);
        }
    }, [editing, textareaRef, onClose, content]);

    const onKeyDown = useCallback(
        (e: KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.key === 'Escape') close();
            textAreaAdjust();
        },
        [close, textAreaAdjust]
    );

    useEffect(() => {
        if (
            editing &&
            textareaRef.current &&
            document.activeElement !== textareaRef.current
        ) {
            const l = textareaRef.current.value.length;
            textareaRef.current.selectionStart = l;
            textareaRef.current.selectionEnd = l;
            textareaRef.current.focus();
            textAreaAdjust();
        }
    }, [editing, textareaRef, textAreaAdjust]);

    useEffect(() => {
        const handler = (event: globalThis.MouseEvent) => {
            if (
                containerRef.current &&
                !containerRef.current.contains(event.target as Node)
            ) {
                close();
            }
        };

        window.addEventListener('mousedown', handler);
        return () => window.removeEventListener('mousedown', handler);
    }, [containerRef, close]);

    return (
        <div
            className={cn(
                'relative mb-6 break-inside-avoid rounded-4xl transition-transform',
                editing || loading
                    ? 'scale-105 shadow-lg'
                    : 'hover:scale-105 hover:shadow-lg active:scale-100'
            )}
            ref={containerRef}
        >
            {loading && (
                <div className="pointer-events-all absolute left-0 top-0 z-20 flex h-full w-full items-center justify-center rounded-4xl backdrop-brightness-75">
                    <Loader2 className="animate-spin text-white" size={40} />
                </div>
            )}
            <button
                className="absolute right-0 top-0 z-10 m-4 border-none bg-transparent p-0 text-white outline-none"
                onClick={onDelete}
            >
                <X size={30} />
            </button>
            <button
                className={cn(
                    'relative flex aspect-square w-full cursor-pointer flex-col items-start rounded-4xl border-none px-10 py-14 text-left text-2xl text-dark outline-none',
                    style({ color })
                )}
                onClick={onClick}
            >
                {editing ? (
                    <textarea
                        ref={textareaRef}
                        placeholder="Enter the content for your sticky here"
                        className={cn(
                            'scrollbar-hide w-full max-w-full resize-none whitespace-pre-line break-words bg-transparent text-2xl text-dark placeholder-gray-600 outline-none'
                        )}
                        onKeyDown={onKeyDown}
                        defaultValue={content}
                    />
                ) : (
                    <p className="max-w-full whitespace-pre-line break-words">
                        {content}
                    </p>
                )}
            </button>
        </div>
    );
}
