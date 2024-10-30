<script lang="ts">
  import { type CVAProp, cn } from "$lib/utils";
  import type { Tag } from "$schema/tag";
  import { cva } from "class-variance-authority";
  import { X } from "lucide-svelte";

  const style = cva("", {
    variants: {
      color: {
        white: "bg-white text-black",
        black: "bg-black text-white",
      },
      size: {
        small: "text-xs",
        big: "text-sm",
      },
    },
    defaultVariants: {
      color: "white",
      size: "small",
    },
  });

  type TagColor = CVAProp<typeof style, "color">;
  type TagSize = CVAProp<typeof style, "size">;

  type Props = {
    tag: Pick<Tag, "name">;
    editing?: boolean;
    color?: TagColor;
    size?: TagSize;
    onClick?: () => void;
    onRemove?: () => void;
  };

  const { tag, editing, color, size, onClick, onRemove }: Props = $props();

  let removeContainerElement: HTMLDivElement | null = null;

  const handleClick = (e: MouseEvent) => {
    if (
      onClick &&
      removeContainerElement &&
      !removeContainerElement.contains(e.target as Node)
    ) {
      onClick();
    }
  };
</script>

<button
  type="button"
  class={cn(
    "flex items-center gap-1 rounded-full py-1 pl-3 text-xs",
    style({ color, size }),
    onClick && "cursor-pointer"
  )}
  onclick={handleClick}
>
  {tag.name}

  <div class="flex items-center pl-0.5 pr-2" bind:this={removeContainerElement}>
    {#if editing && onRemove}
      <button type="button" onclick={onRemove}>
        <X size={12} class="opacity-70" />
      </button>
    {/if}
  </div>
</button>
