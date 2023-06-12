import { NextResponse } from "next/server";
import { surreal } from "../../surreal";
import { Sticky, validateId, validateSticky } from "../lib";

// CURL: curl http://localhost:3000/api/sticky/sticky:p6rht9dfrkrfi78n11k3
// This is the output of curl command: { success: true, sticky: {"content":"test","id":"sticky:p6rht9dfrkrfi78n11k3","color":"pink"} }
export async function GET(_: Request, { params }: { params: { id: string; } }) {
    const { id, ...validation } = validateId(params.id);
    if (validation.error) return validation.error;

    const result = await surreal.select(`sticky:${id}`);
    return NextResponse.json({
        success: true,
        sticky: result[0]
    });
}

// CURL: curl -X PATCH -H "Content-Type: application/json" -d '{"color":"pink","content":"test"}' http://localhost:3001/api/sticky/sticky:p6rht9dfrkrfi78n11k3
// This is the output of curl command: { success: true, sticky: {"content":"test","id":"sticky:p6rht9dfrkrfi78n11k3","color":"pink"} }
export async function PATCH(request: Request, { params }: { params: { id: string; } }) {
    console.log('hello?', params.id)
    const { id, ...validation } = validateId(params.id);
    console.log(params.id, id)
    if (validation.error) return validation.error;

    const sticky = await request.json() as Partial<Pick<Sticky, 'color' | 'content'>>;
    const error = validateSticky(sticky);
    if (error) return error;

    const update: Partial<Sticky> = { updated: new Date() };
    if (sticky.color) update.color = sticky.color;
    if (sticky.content) update.content = sticky.content;

    const result = await surreal.merge(`sticky:${id}`, update);
    return NextResponse.json({
        success: true,
        sticky: result[0]
    });
}

// CURL: curl -X DELETE http://localhost:3001/api/sticky/sticky:p6rht9dfrkrfi78n11k3
// This is the output of curl command: { success: true, sticky: {"content":"test","id":"sticky:p6rht9dfrkrfi78n11k3","color":"pink"} }
export async function DELETE(request: Request, { params }: { params: { id: string; } }) {
    const { id, ...validation } = validateId(params.id);
    if (validation.error) return validation.error;

    const result = await surreal.delete(`sticky:${id}`);
    return NextResponse.json({
        success: true,
        sticky: result[0]
    });
}