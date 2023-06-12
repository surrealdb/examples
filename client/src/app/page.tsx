import { Sticky } from "@/components/sticky";

export default function Home() {
  return (
    <div className="w-full grid grid-cols-3 gap-6 py-16">
      <Sticky color="pink">
        Hello world!
      </Sticky>
      <Sticky color="pink">
        Hello world!
      </Sticky>
      <Sticky color="purple">
        Hello world!
      </Sticky>
      <Sticky color="pink">
        Hello world!
      </Sticky>
      <Sticky color="purple">
        Hello world!
      </Sticky>
      <Sticky color="pink">
        Hello world!
      </Sticky>
    </div>
  );
}