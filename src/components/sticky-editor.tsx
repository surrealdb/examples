'use client';

import { Sticky } from '@/app/api/sticky/lib';
import { cn } from '@/lib/utils';
import * as Dialog from '@radix-ui/react-dialog';
import { cva } from 'class-variance-authority';
import { X } from 'lucide-react';
import React, {
    KeyboardEvent,
    ReactNode,
    createRef,
    useCallback,
    useState,
} from 'react';
import { animated, config, useTransition } from 'react-spring';

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

export function StickyEditor({
    title,
    onSubmit,
    initialValue,
    color,
    children,
}: {
    title: string;
    onSubmit: (sticky: Pick<Sticky, 'color' | 'content'>) => unknown;
    initialValue?: string;
    color: StickyColor;
    children: ReactNode;
}) {
    const ref = createRef<HTMLTextAreaElement>();
    const [open, setOpen] = useState(false);

    // The enter key is used to submit the sticky editor
    // So we need to listen for that, but only when the shift key is not pressed
    // When shift is pressed, we still want to go for a newline :)
    const onKeyDown = useCallback(
        (e: KeyboardEvent<HTMLTextAreaElement>) => {
            if (e.keyCode == 13 && e.shiftKey == false) {
                // Detected! Prevent a newline from being created
                e.preventDefault();

                // Check for fault input
                if (!ref.current)
                    return alert('Internal error (input not mounted)');
                if (!ref.current.value.trim())
                    return alert('The sticky is empty!');

                onSubmit({ color, content: ref.current.value.trim() });
                setOpen(false);
            }
        },
        [ref, color, onSubmit]
    );

    const transitions = useTransition(open, {
        from: { opacity: 0, y: -10 },
        enter: { opacity: 1, y: 0 },
        config: config.stiff,
    });

    return (
        <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger asChild>{children}</Dialog.Trigger>
            {transitions((styles, item) =>
                item ? (
                    <Dialog.Portal>
                        <Dialog.Overlay forceMount asChild>
                            <animated.div
                                className="fixed left-0 top-0 z-10 h-screen w-screen backdrop-blur-lg backdrop-brightness-75"
                                style={{
                                    opacity: styles.opacity,
                                }}
                            />
                        </Dialog.Overlay>
                        <Dialog.Content forceMount asChild>
                            <animated.div
                                style={styles}
                                className={cn(
                                    'fixed bottom-0 left-0 right-0 top-0 z-20 m-auto flex w-[90%] max-w-2xl flex-col items-center justify-center gap-5 rounded-4xl border-none p-8 px-8 py-10 shadow-2xl outline-none max-sm:h-[50%] sm:aspect-square sm:px-12 sm:py-16',
                                    style({ color })
                                )}
                            >
                                <div className="flex w-full items-center justify-between gap-8 text-white">
                                    <h1 className="whitespace-nowrap text-3xl">
                                        {title}
                                    </h1>
                                    <Dialog.Close asChild>
                                        <button className="border-none bg-transparent p-0 outline-none">
                                            <X size={28} />
                                        </button>
                                    </Dialog.Close>
                                </div>

                                <textarea
                                    ref={ref}
                                    placeholder="Enter the content for your sticky here"
                                    className="w-full flex-grow bg-transparent text-2xl placeholder-gray-600 outline-none"
                                    onKeyDown={onKeyDown}
                                    defaultValue={initialValue}
                                />
                            </animated.div>
                        </Dialog.Content>
                    </Dialog.Portal>
                ) : null
            )}
        </Dialog.Root>
    );
}
