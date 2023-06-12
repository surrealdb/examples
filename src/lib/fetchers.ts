'use client';

import { Sticky } from "@/app/api/sticky/lib";

export async function fetchStickies(): Promise<{
    success: boolean;
    stickies: Sticky[];
}> {
    return await (await fetch('/api/sticky')).json();
}

export async function fetchSticky(id: string): Promise<{
    success: boolean;
    sticky?: Sticky;
}> {
    return await (await fetch(`/api/sticky/${id}`)).json();
}

export async function createSticky(
    payload: Pick<Sticky, 'color' | 'content'>
): Promise<{
    success: boolean;
    sticky?: Sticky;
}> {
    return await (await fetch('/api/sticky', {
        method: 'post',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })).json();
}

export async function updateSticky(
    id: string, 
    payload: Partial<Pick<Sticky, 'color' | 'content'>>
): Promise<{
    success: boolean;
    sticky?: Sticky;
}> {
    return await (await fetch(`/api/sticky/${id}`, {
        // Not sure why, but when the method was lowercase nextjs will thrown a HTTP 400 error...
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })).json();
}

export async function deleteSticky(id: string): Promise<{
    success: boolean;
    sticky?: Sticky;
}> {
    return await (await fetch(`/api/sticky/${id}`, {
        method: 'delete',
    })).json();
}