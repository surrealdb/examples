import { Sticky } from "@/components/sticky";

export default async function Home() {
  const raw = await fetch('http://127.0.0.1:3001/notes');
  const stickies = await raw.json() as { color: 'pink' | 'purple', content: string, id: string }[];

  return (
    <div className="w-full grid grid-cols-3 gap-6 py-16">
      {stickies.map(({ id, content, color }) => (
        <Sticky key={id} color={color}>
          {content}
        </Sticky>
      ))}
    </div>
  );
}