import { Error } from '@/components/error';
import { cn } from '@/lib/utils';
import React, { InputHTMLAttributes, forwardRef } from 'react';

export const Input = forwardRef<
    HTMLInputElement,
    InputHTMLAttributes<HTMLInputElement> & {
        errorMessage?: string;
    }
>(({ id, className, placeholder, errorMessage, ...props }, ref) => {
    return (
        <div className="relative w-full">
            <input
                id={id}
                className={cn(
                    'peer w-full rounded-md bg-transparent pt-3 text-lg text-white outline-none placeholder:text-white placeholder:opacity-80',
                    className
                )}
                placeholder=""
                ref={ref}
                {...props}
            />
            <label
                htmlFor={id}
                className="pointer-events-none absolute left-0 top-1 z-10 origin-[0] -translate-y-3 scale-50 transform text-white opacity-50 duration-200 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-placeholder-shown:opacity-80 peer-focus:-translate-y-3 peer-focus:scale-50 peer-focus:opacity-80"
            >
                {placeholder}
            </label>
            <Error message={errorMessage} />
        </div>
    );
});

Input.displayName = 'Input';
