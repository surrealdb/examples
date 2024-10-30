<script lang="ts">
  import "../app.css";
  import Footer from "$components/Footer.svelte";
  import Navbar from "$components/Navbar.svelte";
  import TagPickerDialog from "$components/TagPickerDialog.svelte";
  import { isTagPickerDialogOpened } from "$stores/dialog.store";
  const { children } = $props();
</script>

<svelte:head>
  <title>SurrealDB stickies</title>
  <meta
    name="description"
    content="Create, edit and remove stickies! Powered by SurrealDB!"
  />
</svelte:head>

<div class="flex h-screen flex-col bg-dots">
  <div
    class="mx-auto flex w-full max-w-screen-xl flex-grow flex-col px-8 sm:px-24"
  >
    {#if $isTagPickerDialogOpened}
      <TagPickerDialog />
    {/if}

    <Navbar />
    <!-- We use the content of the page to grow so that the footer is always down the bottom -->
    <div class="flex-grow">
        {@render children()}
    </div>
    <Footer />
  </div>
</div>
