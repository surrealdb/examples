import { NextResponse } from 'next/server';
import { surreal } from '../surreal';
import { Sticky, validateSticky } from './lib';

// CURL: curl http://localhost:3000/api/sticky
// This is the output of curl command: { success: true, stickies: [{"content":"test","id":"sticky:p6rht9dfrkrfi78n11k3","color":"pink"}] }
export async function GET() {
    // Custom select query for ordering
    const result = await surreal.query(
        'SELECT * FROM sticky ORDER BY updated DESC'
    );
    return NextResponse.json({
        success: true,
        stickies: result?.[0]?.result ?? [],
    });
}

// CURL: curl -X POST -H "Content-Type: application/json" -d '{"color":"pink","content":"test"}' http://localhost:3001/api/sticky
// This is the output of curl command: { success: true, sticky: {"content":"test","id":"sticky:p6rht9dfrkrfi78n11k3","color":"pink"} }
export async function POST(request: Request) {
    const sticky = (await request.json()) as Pick<Sticky, 'color' | 'content'>;
    const error = validateSticky(sticky);
    if (error) return error;

    const { content, color } = sticky;
    const created = new Date();
    const updated = created;
    const result = await surreal.create('sticky', {
        content,
        color,
        created,
        updated,
    });
    return NextResponse.json({
        success: true,
        sticky: result[0],
    });
}
