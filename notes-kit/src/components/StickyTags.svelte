<script lang="ts">
  import type { Tag } from "$schema/tag";
  import { openDialog } from "$stores/dialog.store";
  import { Plus } from "lucide-svelte";
  import TagComponent from "./Tag.svelte";

  type Props = {
    editing?: boolean;
    tags: Pick<Tag, "id" | "name">[];
    onAssignTag?: (tag: Tag["id"]) => unknown;
    onUnassignTag?: (tag: Tag["id"]) => unknown;
  };

  const { editing, tags, onAssignTag, onUnassignTag }: Props = $props();
</script>

<div class="flex items-center gap-2 pb-3">
  {#if tags.length > 0}
    {#each tags as tag (tag.id)}
      <TagComponent
        {editing}
        {tag}
        onRemove={onUnassignTag ? () => onUnassignTag(tag.id) : undefined}
      />
    {/each}
  {:else}
    <p class="text-sm text-white opacity-50">No tags</p>
  {/if}

  {#if editing && onAssignTag}
    <button
      type="button"
      class="flex items-center gap-1 rounded-full bg-white px-2 py-1 text-xs"
      onclick={() => openDialog("TagPicker")}
    >
      <Plus size={14} />
    </button>
  {/if}
</div>
