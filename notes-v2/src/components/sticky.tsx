'use client';

import { useDeleteSticky, useUpdateSticky } from '@/lib/hooks/stickies';
import { useStickiesStore } from '@/lib/stores/stickies';
import { CVAProp, cn } from '@/lib/utils';
import { Tag } from '@/schema/tag';
import { cva } from 'class-variance-authority';
import { Loader2, Plus, X } from 'lucide-react';
import React, {
    KeyboardEvent,
    ReactNode,
    createRef,
    useCallback,
    useEffect,
    useState,
} from 'react';

import {
    useAssignTag,
    useAssignedTags,
    useUnassignTag,
} from '@/lib/hooks/tag_assignments';
import { Sticky as StickySchema } from '@/schema/sticky';
import { Tag as RenderTag } from './tag';
import { TagPicker } from './tag-picker';

export const style = cva('', {
    variants: {
        color: {
            purple: 'bg-purple-sticky',
            pink: 'bg-pink-sticky',
        },
    },
});

export type StickyColor = CVAProp<typeof style, 'color'>;

export function Sticky({
    id,
    color,
    content,
}: {
    id: StickySchema['id'];
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

    const { trigger: assignTag } = useAssignTag(id);
    const { trigger: unassignTag } = useUnassignTag(id);
    const { data: tags } = useAssignedTags(id);

    const submit = useCallback(
        async (content?: string) => {
            if (typeof content == 'string') {
                setLoading(true);
                const sticky = await updateSticky({ color, content });
                if (sticky) mergeStickies([sticky]);
            }

            setEditing(null);
            setLoading(false);
        },
        [color, updateSticky, mergeStickies, setEditing]
    );

    const onDelete = useCallback(async () => {
        const sticky = await deleteSticky();
        if (sticky) deleteStickyFromCache(sticky.id);
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
            onAssignTag={(tag) => assignTag(tag)}
            onUnassignTag={(tag) => unassignTag(tag)}
            tags={tags}
        />
    );
}

export function StickyFramework({
    color,
    content,
    onClick,
    onClose,
    onDelete,
    onAssignTag,
    onUnassignTag,
    children,
    editing,
    loading,
    tags,
}: {
    color: StickyColor;
    content?: string;
    children?: ReactNode;
    onClick?: () => unknown;
    onClose?: (content?: string) => unknown;
    onDelete?: () => unknown;
    onAssignTag?: (tag: Tag['id']) => unknown;
    onUnassignTag?: (tag: Tag['id']) => unknown;
    editing?: boolean;
    loading?: boolean;
    tags?: Pick<Tag, 'id' | 'name'>[];
}) {
    const tagPickerRef = createRef<HTMLDivElement>();
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
                !containerRef.current.contains(event.target as Node) &&
                (tagPickerRef.current
                    ? !tagPickerRef.current.contains(event.target as Node)
                    : true)
            ) {
                close();
            }
        };

        window.addEventListener('mousedown', handler);
        return () => window.removeEventListener('mousedown', handler);
    }, [containerRef, tagPickerRef, close]);

    function StickyTags() {
        return (
            tags && (
                <div className="flex items-center gap-2 pb-3">
                    {tags.length > 0 ? (
                        tags.map((tag) => (
                            <RenderTag
                                key={tag.id}
                                onRemove={
                                    onUnassignTag
                                        ? () => onUnassignTag(tag.id)
                                        : undefined
                                }
                                {...{
                                    tag,
                                    editing,
                                }}
                            />
                        ))
                    ) : (
                        <p className="text-sm text-white opacity-50">No tags</p>
                    )}
                    {editing && onAssignTag && (
                        <TagPicker ref={tagPickerRef} onPick={onAssignTag}>
                            <div className="flex items-center gap-1 rounded-full bg-white px-2 py-1 text-xs">
                                <Plus size={14} />
                            </div>
                        </TagPicker>
                    )}
                </div>
            )
        );
    }

    const contentContainerClasses = cn(
        'relative flex aspect-square w-full flex-col items-start rounded-4xl border-none px-10 py-14 text-left text-2xl text-dark outline-none',
        style({ color }),
        (!onClick || editing) && 'cursor-text'
    );

    return (
        <div
            className={cn(
                'relative mb-6 break-inside-avoid rounded-4xl transition-transform',
                editing || loading
                    ? 'scale-105 shadow-lg'
                    : 'hover:scale-105 hover:shadow-lg' +
                          (onClick ? 'active:scale-100' : '')
            )}
            ref={containerRef}
        >
            {loading && (
                <div className="pointer-events-all absolute left-0 top-0 z-20 flex h-full w-full items-center justify-center rounded-4xl backdrop-brightness-75">
                    <Loader2 className="animate-spin text-white" size={40} />
                </div>
            )}
            {onDelete && (
                <button
                    className="absolute right-0 top-0 z-10 m-4 border-none bg-transparent p-0 text-white outline-none"
                    onClick={onDelete}
                >
                    <X size={30} />
                </button>
            )}
            {!editing && !children ? (
                <button className={contentContainerClasses} onClick={onClick}>
                    <StickyTags />
                    <p className="max-w-full whitespace-pre-line break-words">
                        {content}
                    </p>
                </button>
            ) : (
                <div className={contentContainerClasses}>
                    <StickyTags />
                    {children ?? (
                        <textarea
                            ref={textareaRef}
                            placeholder="Enter the content for your sticky here"
                            className={cn(
                                'scrollbar-hide w-full max-w-full resize-none whitespace-pre-line break-words bg-transparent text-2xl text-dark placeholder-gray-600 outline-none'
                            )}
                            onKeyDown={onKeyDown}
                            defaultValue={content}
                        />
                    )}
                </div>
            )}
        </div>
    );
}
