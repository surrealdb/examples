'use client';

import { Sticky } from "@/components/sticky";
import { useStickies } from "@/lib/hooks";
import { Loader2 } from "lucide-react";

export default function Home() {
    const { data, isLoading } = useStickies();
  
    const message = data?.stickies.length == 0 ? "Create a sticky!" : undefined;

    return isLoading ? (
      <div className="w-full h-full flex justify-center items-center">
        <h1 className="text-2xl flex gap-4 items-center">
          <Loader2 className="animate-spin" />
          Loading stickies
        </h1>
      </div>
    ) : message ? (
      <div className="w-full h-full flex justify-center items-center">
        <h1 className="text-2xl">
          {message}
        </h1>
      </div>
    ) : (
      <div className="w-full grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 sm:py-16">
        {data?.stickies.map(({ id, content, color }) => (
          <Sticky key={id} id={id} color={color} content={content} />
        ))}
      </div>
    );
  }