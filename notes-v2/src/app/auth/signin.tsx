'use client';

import { Error } from '@/components/error';
import { StickyFramework } from '@/components/sticky';
import { useStickies } from '@/lib/hooks/stickies';
import { useAuth } from '@/lib/stores/auth';
import { useStickiesStore } from '@/lib/stores/stickies';
import { database, namespace, surreal } from '@/lib/surreal';
import { zodResolver } from '@hookform/resolvers/zod';
import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Input } from './input';

const Schema = z.object({
    username: z.string().min(1, 'Please enter your username'),
    password: z.string().min(1, 'Please enter your password'),
});

type Schema = z.infer<typeof Schema>;

export default function Signin() {
    const { refresh: refreshAuth } = useAuth();
    const { mutate: refreshStickies } = useStickies();
    const { reset } = useStickiesStore();
    const {
        register,
        handleSubmit,
        formState: { errors },
        setError,
    } = useForm<Schema>({
        resolver: zodResolver(Schema),
    });

    const handler = handleSubmit(async ({ username, password }) => {
        const token = await surreal
            .signin({
                NS: namespace,
                DB: database,
                SC: 'user',
                username,
                password,
            })
            .catch(() => undefined);

        if (token) {
            reset();
            localStorage.setItem('token', token);
            await refreshAuth();
            await refreshStickies();
        } else {
            setError('root', {
                type: 'custom',
                message: 'Invalid credentials',
            });
        }
    });

    return (
        <StickyFramework
            color="pink"
            tags={[{ id: 'tag:signin', name: 'Signin' }]}
        >
            <form className="flex w-full flex-col gap-2" onSubmit={handler}>
                <div className="w-full gap-1">
                    <Input
                        id="signin_username"
                        placeholder="Username"
                        errorMessage={errors.username?.message}
                        {...register('username')}
                    />
                    <Input
                        id="signin_password"
                        placeholder="Password"
                        type="password"
                        errorMessage={errors.password?.message}
                        {...register('password')}
                    />
                </div>

                <div>
                    <button className="text-lg hover:underline">
                        Continue
                    </button>
                    <Error message={errors.root?.message} />
                </div>
            </form>
        </StickyFramework>
    );
}
