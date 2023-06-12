"use client";

import { cva } from "class-variance-authority";
import { Plus, X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";

const style = cva(
  "w-12 h-12 flex justify-center items-center rounded-xl outline-none border-none text-white",
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
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className={style({ color })}>
          <Plus />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed backdrop-blur-sm w-screen h-screen z-10 top-0 left-0" />
        <Dialog.Content className="fixed shadow-xl p-8 bg-white w-96 h-96 px-8 py-10 rounded-4xl z-20 top-0 left-0 bottom-0 right-0 m-auto flex flex-col gap-4">
          <div className="flex justify-between items-center gap-16">
            <h1 className="text-3xl whitespace-nowrap">Add sticky</h1>
            <Dialog.Close>
              <button className="p-0 outline-none border-none bg-transparent text-dark">
                <X size={28} />
              </button>
            </Dialog.Close>
          </div>

          <textarea 
            placeholder="Enter the content for your sticky here" 
            className="text-2xl outline-none flex-grow"
            onKeyDown={(e) => {
            if(e.keyCode == 13 && e.shiftKey == false) {
                e.preventDefault();
                alert('submitted')
            }
            }} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
