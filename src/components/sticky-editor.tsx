"use client";

import { cva } from "class-variance-authority";
import { X } from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import {
  KeyboardEvent,
  ReactNode,
  createRef,
  useCallback,
  useState,
} from "react";
import { Sticky } from "@/app/api/sticky/lib";
import { useTransition, animated, config } from "react-spring";

const style = cva(
  "justify-center items-center outline-none border-none fixed shadow-2xl p-8 w-[90%] max-w-2xl max-sm:h-[50%] sm:aspect-square px-8 py-10 sm:px-12 sm:py-16 rounded-4xl z-20 top-0 left-0 bottom-0 right-0 m-auto flex flex-col gap-5",
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

export function StickyEditor({
  title,
  onSubmit,
  initialValue,
  color,
  children,
}: {
  title: string;
  onSubmit: (sticky: Pick<Sticky, "color" | "content">) => unknown;
  initialValue?: string;
  color: StickyColor;
  children: ReactNode;
}) {
  const ref = createRef<HTMLTextAreaElement>();
  const [open, setOpen] = useState(false);
  const onKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.keyCode == 13 && e.shiftKey == false) {
        e.preventDefault();
        if (!ref.current) return alert("Internal error (input not mounted)");
        if (!ref.current.value.trim()) return alert("The sticky is empty!");
        onSubmit({ color, content: ref.current.value.trim() });

        setOpen(false);
      }
    },
    [ref, color, onSubmit]
  );

  const transitions = useTransition(open, {
    from: { opacity: 0, y: -10 },
    enter: { opacity: 1, y: 0 },
    config: config.stiff,
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>{children}</Dialog.Trigger>
      {transitions((styles, item) =>
        item ? (
          <Dialog.Portal>
            <Dialog.Overlay forceMount asChild>
              <animated.div
                className="fixed backdrop-blur-lg backdrop-brightness-75 w-screen h-screen z-10 top-0 left-0"
                style={{
                  opacity: styles.opacity,
                }}
              />
            </Dialog.Overlay>
            <Dialog.Content forceMount asChild>
              <animated.div style={styles} className={style({ color })}>
                <div className="flex w-full justify-between items-center gap-8 text-white">
                  <h1 className="text-3xl whitespace-nowrap">{title}</h1>
                  <Dialog.Close asChild>
                    <button className="p-0 outline-none border-none bg-transparent">
                      <X size={28} />
                    </button>
                  </Dialog.Close>
                </div>

                <textarea
                  ref={ref}
                  placeholder="Enter the content for your sticky here"
                  className="text-2xl w-full outline-none flex-grow bg-transparent placeholder-gray-600"
                  onKeyDown={onKeyDown}
                  defaultValue={initialValue}
                />
              </animated.div>
            </Dialog.Content>
          </Dialog.Portal>
        ) : null
      )}
    </Dialog.Root>
  );
}
