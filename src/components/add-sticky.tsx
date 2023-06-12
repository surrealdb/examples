"use client";

import { cva } from "class-variance-authority";
import { Plus } from "lucide-react";
import { useCreateSticky } from "@/lib/hooks";
import { StickyEditor } from "./sticky-editor";

const style = cva(
  "w-10 h-10 sm:w-12 sm:h-12 flex justify-center items-center rounded-xl outline-none border-none text-white hover:scale-110 transition-transform",
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

export function AddSticky({ color }: { color: StickyColor }) {
  const { trigger: createSticky } = useCreateSticky();

  return (
    <StickyEditor title="Add sticky" color={color} onSubmit={createSticky}>
      <button className={style({ color })}>
        <Plus />
      </button>
    </StickyEditor>
  );
}
