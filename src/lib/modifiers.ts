'use client';

import { Sticky } from '@/app/api/sticky/lib';

const processRawSticky = ({ updated, created, ...rest }: Sticky) => ({
    ...rest,
    created: new Date(created),
    updated: new Date(updated),
});

// GET /api/sticky
// project://src/app/api/sticky/route.ts#7
export async function fetchStickies() {
    const res: {
        success: boolean;
        stickies: Sticky[];
    } = await (await fetch('/api/sticky')).json();

    res.stickies = res.stickies.map(processRawSticky);
    return res;
}

// GET /api/sticky/....
// project://src/app/api/sticky/[id]/route.ts#7
export async function fetchSticky(id: string) {
    const res: {
        success: boolean;
        sticky?: Sticky;
    } = await (await fetch(`/api/sticky/${id}`)).json();

    if (res.sticky) res.sticky = processRawSticky(res.sticky);
    return res;
}

// POST /api/sticky
// project://src/app/api/sticky/route.ts#20
export async function createSticky(payload: Pick<Sticky, 'color' | 'content'>) {
    const res: {
        success: boolean;
        sticky?: Sticky;
    } = await (
        await fetch('/api/sticky', {
            method: 'post',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })
    ).json();

    if (res.sticky) res.sticky = processRawSticky(res.sticky);
    return res;
}

// PATCH /api/sticky/....
// project://src/app/api/sticky/[id]/route.ts#20
export async function updateSticky(
    id: string,
    payload: Partial<Pick<Sticky, 'color' | 'content'>>
) {
    const res: {
        success: boolean;
        sticky?: Sticky;
    } = await (
        await fetch(`/api/sticky/${id}`, {
            // Not sure why, but when the method was lowercase nextjs will thrown a HTTP 400 error...
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        })
    ).json();

    if (res.sticky) res.sticky = processRawSticky(res.sticky);
    return res;
}

// DELETE /api/sticky/....
// project://src/app/api/sticky/[id]/route.ts#48
export async function deleteSticky(id: string) {
    const res: {
        success: boolean;
        sticky?: Sticky;
    } = await (
        await fetch(`/api/sticky/${id}`, {
            method: 'delete',
        })
    ).json();

    if (res.sticky) res.sticky = processRawSticky(res.sticky);
    return res;
}
