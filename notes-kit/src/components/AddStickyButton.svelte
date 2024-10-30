<script lang="ts">
  import { type CVAProp, cn } from "$lib/utils";
  import { createNewSticky } from "$stores/stickies.store";
  import { cva } from "class-variance-authority";
  import { Plus } from "lucide-svelte";

  const style = cva("", {
    variants: {
      color: {
        purple: "bg-purple-sticky",
        pink: "bg-pink-sticky",
      },
    },
  });

  type StickyColor = CVAProp<typeof style, "color">;

  type Props = {
    color: StickyColor;
  };

  const { color }: Props = $props();

  const handleClick = async () => {
    await createNewSticky(color);
  };
</script>

<button
  type="button"
  class={cn(
    "flex h-10 w-10 items-center justify-center rounded-xl border-none text-white outline-none transition-transform hover:scale-110 sm:h-12 sm:w-12",
    style({ color })
  )}
  onclick={handleClick}
>
  <Plus />
</button>
