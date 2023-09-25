import { CVAProp, cn } from '@/lib/utils';
import { Tag } from '@/schema/tag';
import { cva } from 'class-variance-authority';
import { X } from 'lucide-react';
import React, { createRef } from 'react';

export const style = cva('', {
    variants: {
        color: {
            white: 'bg-white text-black',
            black: 'bg-black text-white',
        },
        size: {
            small: 'text-xs',
            big: 'text-sm',
        },
    },
    defaultVariants: {
        color: 'white',
        size: 'small',
    },
});

export type TagColor = CVAProp<typeof style, 'color'>;
export type TagSize = CVAProp<typeof style, 'size'>;

function RenderTag({
    tag: { name },
    editing,
    color,
    size,
    onRemove,
    onClick,
}: {
    tag: Pick<Tag, 'name'>;
    editing?: boolean;
    color?: TagColor;
    size?: TagSize;
    onRemove?: () => void;
    onClick?: () => void;
}) {
    const removeContainerRef = createRef<HTMLDivElement>();

    return (
        <div
            className={cn(
                'flex items-center gap-1 rounded-full py-1 pl-3 text-xs',
                style({ color, size }),
                onClick && 'cursor-pointer'
            )}
            onClick={(e) => {
                if (
                    onClick &&
                    removeContainerRef.current &&
                    !removeContainerRef.current.contains(e.target as Node)
                ) {
                    onClick();
                }
            }}
        >
            {name}
            <div
                className="flex items-center pl-0.5 pr-2"
                ref={removeContainerRef}
            >
                {editing && onRemove && (
                    <button onClick={onRemove}>
                        <X size={12} className="opacity-70" />
                    </button>
                )}
            </div>
        </div>
    );
}

export { RenderTag as Tag };
