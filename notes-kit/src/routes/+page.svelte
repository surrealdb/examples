<script lang="ts">
  import Loading from "$components/Loading.svelte";
  import Signin from "$components/Signin.svelte";
  import Signup from "$components/Signup.svelte";
  import Sticky from "$components/Sticky.svelte";
  import { authenticated, initialized, refreshAuth } from "$stores/auth.store";
  import { loadStickies, sortedStickies } from "$stores/stickies.store";
</script>

{#await refreshAuth()}
  <Loading />
{:then _}
  {#if $initialized && !$authenticated}
    <div class="w-full sm:py-16 md:columns-2 xl:columns-3">
      <Signin />
      <Signup />
    </div>
  {:else}
    {#await loadStickies()}
      <Loading />
    {:then _}
      <div class="w-full sm:py-16 md:columns-2 xl:columns-3">
        {#each $sortedStickies as { id, content, color } (id)}
          <Sticky {id} {color} {content} />
        {/each}
      </div>
    {:catch error}
      <span class="text-red-500">
        <b>An error occured:</b>
        {error}
      </span>
    {/await}
  {/if}
{/await}
