'use client';

import { Error } from '@/components/error';
import { StickyFramework } from '@/components/sticky';
import { useAuth } from '@/lib/stores/auth';
import { useStickiesStore } from '@/lib/stores/stickies';
import { database, namespace, surreal } from '@/lib/surreal';
import { zodResolver } from '@hookform/resolvers/zod';
import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Input } from './input';

const Schema = z.object({
    name: z.string().min(1, 'Please enter your name'),
    username: z.string().min(1, 'Please enter a username'),
    password: z.string().min(8, 'Password must be at least 8 charachters'),
});

type Schema = z.infer<typeof Schema>;

export default function Signup() {
    const { refresh } = useAuth();
    const { reset } = useStickiesStore();
    const {
        register,
        handleSubmit,
        formState: { errors },
        setError,
    } = useForm<Schema>({
        resolver: zodResolver(Schema),
    });

    const handler = handleSubmit(async ({ name, username, password }) => {
        const token = await surreal
            .signup({
                NS: namespace,
                DB: database,
                SC: 'user',
                name,
                username,
                password,
            })
            .catch(() => undefined);

        if (token) {
            reset();
            localStorage.setItem('token', token);
            await refresh();
        } else {
            setError('root', {
                type: 'custom',
                message:
                    'Could not create your account, username might already be taken.',
            });
        }
    });

    return (
        <StickyFramework
            color="purple"
            tags={[{ id: 'tag:signup', name: 'Signup' }]}
        >
            <form className="flex w-full flex-col gap-2" onSubmit={handler}>
                <div className="w-full gap-1">
                    <Input
                        id="signup_name"
                        placeholder="Name"
                        errorMessage={errors.name?.message}
                        {...register('name')}
                    />
                    <Input
                        id="signup_username"
                        placeholder="Username"
                        errorMessage={errors.username?.message}
                        {...register('username')}
                    />
                    <Input
                        id="signup_password"
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
