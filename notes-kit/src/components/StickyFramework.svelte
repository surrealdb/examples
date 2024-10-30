<script lang="ts">
  import { type CVAProp, cn } from "$lib/utils";
  import type { Tag } from "$schema/tag";
  import { cva } from "class-variance-authority";
  import { Loader2, X } from "lucide-svelte";
  import { type Snippet, onMount } from "svelte";
  import StickyTags from "./StickyTags.svelte";

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
    content?: string;
    editing?: boolean;
    loading?: boolean;
    tags?: Pick<Tag, "id" | "name">[];
    onClick?: () => unknown;
    onClose?: (content?: string) => unknown;
    onDelete?: () => unknown;
    onAssignTag?: (tag: Tag["id"]) => unknown;
    onUnassignTag?: (tag: Tag["id"]) => unknown;
    children?: Snippet;
  };

  const {
    color,
    content,
    editing,
    loading,
    tags,
    onClick,
    onClose,
    onDelete,
    onAssignTag,
    onUnassignTag,
    children,
  }: Props = $props();

  const containerClasses = cn(
    "relative mb-6 break-inside-avoid rounded-4xl transition-transform",
    editing || loading
      ? "scale-105 shadow-lg"
      : `hover:scale-105 hover:shadow-lg ${onClick ? "active:scale-100" : ""}`
  );

  const contentContainerClasses = cn(
    "relative flex aspect-square w-full flex-col items-start rounded-4xl border-none px-10 py-14 text-left text-2xl text-dark outline-none",
    style({ color }),
    (!onClick || editing) && "cursor-text"
  );

  let containerElement = $state<HTMLDivElement | null>(null);
  let textareaElement = $state<HTMLTextAreaElement | null>(null);

  const textAreaAdjust = () => {
    if (textareaElement) {
      setTimeout(() => {
        if (textareaElement) {
          textareaElement.style.cssText = "height:auto; padding:0";
          textareaElement.style.cssText = `height:${textareaElement.scrollHeight}px`;
        }
      }, 0);
    }
  };

  const handleClose = () => {
    if (editing) {
      const value = textareaElement?.value?.trim() ?? "";
      onClose?.(value === content ? undefined : value);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      handleClose();
    }
    textAreaAdjust();
  };

  onMount(() => {
    const handler = (event: MouseEvent) => {
      if (
        containerElement &&
        !containerElement.contains(event.target as Node)
      ) {
        handleClose();
      }
    };

    window.addEventListener("mousedown", handler);
    return () => window.removeEventListener("mousedown", handler);
  });
</script>

<div class={containerClasses} bind:this={containerElement}>
  {#if loading}
    <div
      class="pointer-events-all absolute left-0 top-0 z-20 flex h-full w-full items-center justify-center rounded-4xl backdrop-brightness-75"
    >
      <Loader2 class="animate-spin text-white" size={40} />
    </div>
  {/if}

  {#if onDelete}
    <button
      class="absolute right-0 top-0 z-10 m-4 border-none bg-transparent p-0 text-white outline-none"
      onclick={onDelete}
    >
      <X size={30} />
    </button>
  {/if}

  {#if !editing && !children}
    <button class={contentContainerClasses} onclick={onClick}>
      <StickyTags {editing} tags={tags || []} {onAssignTag} {onUnassignTag} />
      <p class="max-w-full whitespace-pre-line break-words">
        {content}
      </p>
    </button>
  {:else}
    <div class={contentContainerClasses}>
      <StickyTags {editing} tags={tags || []} {onAssignTag} {onUnassignTag} />
      {#if !!children}
        {@render children()}
      {:else}
        <textarea
          placeholder="Enter the content for your sticky here"
          class="scrollbar-hide w-full max-w-full resize-none whitespace-pre-line break-words bg-transparent text-2xl text-dark placeholder-gray-600 outline-none"
          value={content}
          bind:this={textareaElement}
          onkeydown={handleKeyDown}
        ></textarea>
      {/if}
    </div>
  {/if}
</div>
