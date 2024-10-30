<script lang="ts">
  import Logo from "$assets/logo.svg";
  import { removeAuthCookie } from "$lib/cookie";
  import { getDb } from "$lib/surreal";
  import { authenticated, refreshAuth, username } from "$stores/auth.store";
  import AddStickyButton from "./AddStickyButton.svelte";

  const signout = async () => {
    const db = await getDb();
    await db.invalidate();
    removeAuthCookie();
    await refreshAuth();
  };
</script>

<div
  class="flex justify-between gap-8 py-20 max-md:flex-col max-md:items-center sm:gap-16"
>
  <img class="max-h-16 w-[auto]" src={Logo} alt="SurrealDB Stickies logo" />

  {#if $authenticated}
    <div class="flex items-center gap-4">
      <button type="button" onclick={signout}>
        signout ({$username})
      </button>
      <AddStickyButton color="pink" />
      <AddStickyButton color="purple" />
    </div>
  {/if}
</div>
