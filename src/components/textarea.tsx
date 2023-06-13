'use client';

import { cn } from '@/lib/utils';
import React, { KeyboardEvent, createRef, useCallback, useEffect } from 'react';

export function Textarea({
    className,
    onSubmit,
    initialValue,
    editing,
    setEditing,
}: {
    className?: string;
    onSubmit?: (content: string) => unknown;
    initialValue?: string;
    editing?: boolean;
    setEditing?: (editing: boolean) => unknown;
}) {
    const ref = createRef<HTMLTextAreaElement>();

    useEffect(() => {
        if (editing && ref.current) {
            ref.current.selectionStart = ref.current.value.length;
            ref.current.selectionEnd = ref.current.value.length;
            ref.current.focus();
        }
    });

    // The enter key is used to submit the sticky editor
    // So we need to listen for that, but only when the shift key is not pressed
    // When shift is pressed, we still want to go for a newline :)
    const onKeyDown = useCallback(
        (e: KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.key === 'Enter' && e.shiftKey === false) {
                // Detected! Prevent a newline from being created
                e.preventDefault();

                // Check for fault input
                if (!ref.current)
                    return alert('Internal error (input not mounted)');
                if (!ref.current.value.trim())
                    return alert('The sticky is empty!');

                onSubmit?.(ref.current.value.trim());
            } else if (e.key === 'Escape') {
                setEditing?.(false);
            }
        },
        [ref, onSubmit, setEditing]
    );

    return (
        <textarea
            ref={ref}
            placeholder="Enter the content for your sticky here"
            className={cn(
                'w-full flex-grow bg-transparent text-2xl text-dark placeholder-gray-600 outline-none',
                className
            )}
            onKeyDown={onKeyDown}
            defaultValue={initialValue}
        />
    );
}
