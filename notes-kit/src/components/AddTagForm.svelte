<script lang="ts">
  import { createTag } from "$lib/api/tags";
  import { zodClient } from "sveltekit-superforms/adapters";
  import { superForm } from "sveltekit-superforms/client";
  import { z } from "zod";
  import ErrorMessage from "./ErrorMessage.svelte";

  const schema = z.object({
    name: z.string().min(1, "Please enter a name for the tag"),
  });

  let isMutating = $state(false);

  const { form, errors, constraints, reset, enhance } = superForm(
    {
      name: "",
    },
    {
      SPA: true,
      validators: zodClient(schema),
      onUpdate: async ({ form: f }) => {
        if (f.valid) {
          isMutating = true;

          await createTag(f.data);
          reset();

          isMutating = false;
        }
      },
    }
  );
</script>

<form use:enhance>
  <div class="flex gap-4">
    <input
      class="flex-grow rounded-md border-2 border-solid border-zinc-400 px-5 py-2"
      placeholder="Tag name"
      aria-invalid={$errors.name ? "true" : undefined}
      bind:value={$form.name}
      {...$constraints.name}
      disabled={isMutating}
      autoFocus
    />
    <button disabled={isMutating}>add</button>
  </div>
  <ErrorMessage message={$errors.name?.[0]} />
</form>
