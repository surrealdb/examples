import { cva } from 'class-variance-authority';

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
