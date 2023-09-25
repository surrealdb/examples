import { useCreateTag, useDeleteTag, useTags } from '@/lib/hooks/tags';
import { Tag } from '@/schema/tag';
import { zodResolver } from '@hookform/resolvers/zod';
import React, {
    ReactNode,
    createRef,
    forwardRef,
    useEffect,
    useState,
} from 'react';
import {
    Button,
    Dialog,
    DialogTrigger,
    Heading,
    Modal,
    ModalOverlay,
} from 'react-aria-components';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Error } from './error';
import { Tag as RenderTag } from './tag';

export const TagPicker = forwardRef<
    HTMLDivElement,
    { children: ReactNode; onPick: (id: Tag['id']) => void }
>(({ children, onPick }, ref) => {
    const [open, setOpen] = useState<boolean>(false);
    const dialogRef = createRef<HTMLDivElement>();
    const { data: tags } = useTags();

    useEffect(() => {
        const handler = (event: globalThis.MouseEvent) => {
            if (
                dialogRef.current &&
                !dialogRef.current.contains(event.target as Node)
            ) {
                // The modal needs to be closed only after the effect for the sticky has been processed.
                // otherwise the modal will close AND the sticky will both be closed unfortunately.
                setTimeout(() => setOpen(false), 1);
            }
        };

        window.addEventListener('mousedown', handler);
        return () => window.removeEventListener('mousedown', handler);
    }, [dialogRef, setOpen]);

    return (
        <DialogTrigger isOpen={open} onOpenChange={setOpen}>
            <Button>{children}</Button>
            <ModalOverlay
                className="pointer-events-all absolute z-40 h-screen w-screen bg-black bg-opacity-75"
                ref={ref}
            >
                <Modal className="fixed left-0 top-0 flex h-screen w-screen items-center justify-center">
                    <Dialog
                        className="w-96 rounded-lg bg-white p-12 shadow-2xl"
                        ref={dialogRef}
                    >
                        <Heading className="mb-4 text-3xl">Tags</Heading>
                        <div className="mb-8">
                            {tags && tags.length ? (
                                <div className="flex flex-wrap gap-1.5">
                                    {tags.map((tag) => (
                                        <TagEditor
                                            key={tag.id}
                                            tag={tag}
                                            onPick={(id) => {
                                                // The modal needs to be closed only after the effect for the sticky has been processed.
                                                // otherwise the modal will close AND the sticky will both be closed unfortunately.
                                                setTimeout(() => {
                                                    setOpen(false);
                                                    onPick(id);
                                                }, 1);
                                            }}
                                        />
                                    ))}
                                </div>
                            ) : (
                                <p>Add some new tags!</p>
                            )}
                        </div>
                        <AddTag />
                    </Dialog>
                </Modal>
            </ModalOverlay>
        </DialogTrigger>
    );
});

TagPicker.displayName = 'TagPicker';

const TagEditor = ({
    tag,
    onPick,
}: {
    tag: Tag;
    onPick: (id: Tag['id']) => void;
}) => {
    const { trigger: onRemove } = useDeleteTag(tag.id);
    return (
        <RenderTag
            tag={tag}
            onRemove={onRemove}
            editing
            color="black"
            size="big"
            onClick={() => onPick(tag.id)}
        />
    );
};

const AddTagSchema = z.object({
    name: z.string().min(1, 'Please enter a name for the tag'),
});

type AddTagSchema = z.infer<typeof AddTagSchema>;

const AddTag = () => {
    const { trigger: addTag, isMutating } = useCreateTag();

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<AddTagSchema>({
        resolver: zodResolver(AddTagSchema),
    });

    const handler = handleSubmit(async ({ name }) => {
        await addTag({ name });
        reset();
    });

    return (
        <form onSubmit={handler}>
            <div className="flex gap-4">
                <input
                    className="flex-grow rounded-md border-2 border-solid border-zinc-400 px-5 py-2"
                    placeholder="Tag name"
                    {...register('name')}
                    disabled={isMutating}
                    autoFocus
                />
                <button disabled={isMutating}>add</button>
            </div>
            <Error message={errors.name?.message} />
            <Error message={errors.root?.message} />
        </form>
    );
};
