import { NextResponse } from "next/server";

export const stickyColors = ['pink', 'purple'] as const;
export type StickyColor = typeof stickyColors[number];
export type Sticky = {
    id: string;
    color: StickyColor;
    content: string;
    created: Date;
    updated: Date;
};

export function validateId(given: string) {
    const id = (given.match(/^(?:sticky:)?([a-z0-9]{20})$/) ?? [])[1];
    if (!id) 
        return {
            id,
            error: NextResponse.json({
                success: false,
                error: "missing_id"
            }, { status: 400 })
        };
    
    return { id };
}

export function validateSticky(sticky: Partial<Pick<Sticky, 'color' | 'content'>>, requireAll = true) {
    if (requireAll && (!sticky.color || !sticky.content))
        return NextResponse.json({
            success: false,
            error: "malformed_sticky"
        }, { status: 400 });

    if (!sticky.content?.trim())
        return NextResponse.json({
            success: false,
            error: "content_empty"
        }, { status: 400 });
        
    if (!stickyColors.includes(sticky?.color as StickyColor))
        return NextResponse.json({
            success: false,
            error: "invalid_color"
        }, { status: 400 });
}