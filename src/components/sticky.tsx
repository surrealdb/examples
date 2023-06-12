"use client";

import { useDeleteSticky, useUpdateSticky } from "@/lib/hooks";
import { cva } from "class-variance-authority";
import { X } from "lucide-react";
import { StickyEditor } from "./sticky-editor";

const style = cva(
  "w-full aspect-square px-10 py-14 rounded-4xl text-dark text-2xl relative cursor-pointer",
  {
    variants: {
      color: {
        purple: "bg-purple-sticky",
        pink: "bg-pink-sticky",
      },
    },
  }
);

export type StickyColor = Exclude<
  Exclude<Parameters<typeof style>[0], undefined>["color"],
  null | undefined
>;

export function Sticky({
  id,
  color,
  content,
}: {
  id: string;
  color: StickyColor;
  content: string;
}) {
  const { trigger: deleteSticky } = useDeleteSticky(id);
  const { trigger: updateSticky } = useUpdateSticky(id);

  return (
    <div className="relative hover:scale-105 transition-transform">
      <button
        className="p-0 outline-none border-none bg-transparent text-white absolute top-0 right-0 m-4 z-10"
        onClick={() => deleteSticky()}
      >
        <X size={30} />
      </button>
      <StickyEditor
        title="Edit sticky"
        onSubmit={updateSticky}
        color={color}
        initialValue={content}
      >
        <div className={style({ color })}>{content}</div>
      </StickyEditor>
    </div>
  );
}
