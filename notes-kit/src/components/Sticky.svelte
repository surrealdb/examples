<script lang="ts">
  import {
    assignTag,
    loadAssignedTags,
    unassignTag,
  } from "$lib/api/tag_assignments";
  import type { Sticky } from "$schema/sticky";
  import type { Tag } from "$schema/tag";
  import {
    deleteExistingSticky,
    editing,
    setEditing,
    updateExistingSticky,
  } from "$stores/stickies.store";
  import { onMount } from "svelte";
  import StickyFramework from "./StickyFramework.svelte";

  type Props = Pick<Sticky, "id" | "color" | "content">;

  let { id, color, content }: Props = $props();

  let loading = $state(false);
  let tags = $state<Tag[]>([]);

  onMount(async () => {
    tags = await loadAssignedTags(id);
  });

  const submit = async (content?: string) => {
    if (typeof content === "string") {
      loading = true;
      await updateExistingSticky(id, { color, content });
    }

    loading = false;
  };

  const handleDelete = async () => {
    await deleteExistingSticky(id);
  };

  const handleAssignTag = async (tag: Tag["id"]) => {
    await assignTag({ sticky: id, tag });
  };

  const handleUnassignTag = async (tag: Tag["id"]) => {
    await unassignTag({ sticky: id, tag });
  };
</script>

<StickyFramework
  {color}
  {content}
  editing={$editing === id}
  {loading}
  {tags}
  onClick={() => setEditing(id)}
  onClose={submit}
  onDelete={handleDelete}
  onAssignTag={(tag) => handleAssignTag(tag)}
  onUnassignTag={(tag) => handleUnassignTag(tag)}
/>
