<script lang="ts">
  import { assignTag } from "$lib/api/tag_assignments";
  import { fetchTags } from "$lib/api/tags";
  import type { Tag } from "$schema/tag";
  import { closeDialog } from "$stores/dialog.store";
  import { editing } from "$stores/stickies.store";
  import { onMount } from "svelte";
  import AddTagForm from "./AddTagForm.svelte";
  import TagEditor from "./TagEditor.svelte";

  let tags = $state<Tag[]>([]);
  let dialogContentElement = $state<HTMLElement | null>(null);

  $effect(() => {
    const handler = (event: MouseEvent) => {
      if (
        dialogContentElement &&
        !dialogContentElement.contains(event.target as Node)
      ) {
        setTimeout(() => closeDialog(), 1);
      }
    };

    window.addEventListener("mousedown", handler);
    return () => window.removeEventListener("mousedown", handler);
  });

  onMount(async () => {
    tags = await fetchTags();
  });

  const handlePick = async (id: Tag["id"]) => {
    if ($editing) {
      await assignTag({ sticky: $editing, tag: id });
    }
  };
</script>

<dialog open class="z-[1000]">
  <div class="fixed left-0 right-0 top-0 bottom-0">
    <div
      class="pointer-events-all absolute z-40 h-screen w-screen bg-black bg-opacity-75"
    >
      <div
        class="fixed left-0 top-0 flex h-screen w-screen items-center justify-center"
      >
        <div
          class="w-96 rounded-lg bg-white p-12 shadow-2xl"
          bind:this={dialogContentElement}
        >
          <h2 class="mb-4 text-3xl">Tags</h2>

          <div class="mb-8">
            {#if tags && tags.length > 0}
              <div class="flex flex-wrap gap-1.5">
                {#each tags as tag (tag.id)}
                  <TagEditor {tag} onPick={handlePick} />
                {/each}
              </div>
            {:else}
              <p>Add some new tags!</p>
            {/if}
          </div>

          <AddTagForm />
        </div>
      </div>
    </div>
  </div>
</dialog>
