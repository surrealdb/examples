import { cva } from 'class-variance-authority';
import { ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export type CVAProp<
    T extends ReturnType<typeof cva>,
    prop extends keyof Exclude<Parameters<T>[0], undefined>
> = Exclude<Exclude<Parameters<T>[0], undefined>[prop], null | undefined>;
