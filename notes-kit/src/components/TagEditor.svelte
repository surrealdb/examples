<script lang="ts">
  import { deleteTag } from "$lib/api/tags";
  import type { Tag } from "$schema/tag";
  import TagComponent from "./Tag.svelte";

  type Props = {
    tag: Tag;
    onPick: (id: Tag["id"]) => void;
  };

  const { tag, onPick }: Props = $props();

  const onRemove = async () => {
    await deleteTag(tag.id);
  };
</script>

<TagComponent
  {tag}
  {onRemove}
  editing
  color="black"
  size="big"
  onClick={() => onPick(tag.id)}
/>
