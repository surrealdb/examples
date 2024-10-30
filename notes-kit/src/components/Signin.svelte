<script lang="ts">
  import { setAuthCookie } from "$lib/cookie";
  import { getDb } from "$lib/surreal";
  import { refreshAuth } from "$stores/auth.store";
  import { loadStickies, resetStickiesState } from "$stores/stickies.store";
  import { zodClient } from "sveltekit-superforms/adapters";
  import { setMessage, superForm } from "sveltekit-superforms/client";
  import { z } from "zod";
  import ErrorMessage from "./ErrorMessage.svelte";
  import Input from "./Input.svelte";
  import StickyFramework from "./StickyFramework.svelte";

  const schema = z.object({
    username: z.string().min(1, "Please enter your username"),
    password: z.string().min(1, "Please enter your password"),
  });

  const { form, message, errors, constraints, enhance } = superForm(
    {
      username: "",
      password: "",
    },
    {
      SPA: true,
      validators: zodClient(schema),
      onUpdate: async ({ form: f }) => {
        if (f.valid) {
          const db = await getDb();
          const token = await db
            .signin({
              namespace: db.connection?.connection.namespace,
              database: db.connection?.connection.database,
              access: "user",
              variables: f.data,
            })
            .catch(() => undefined);

          if (token) {
            resetStickiesState();
            setAuthCookie(token);
            await refreshAuth();
            await loadStickies();
          } else {
            setMessage(f, "Invalid credentials.");
          }
        }
      },
    }
  );
</script>

<StickyFramework color="pink" tags={[{ id: "tag:signin", name: "Signin" }]}>
  <form class="flex w-full flex-col gap-2" use:enhance>
    <div class="w-full gap-1">
      <Input
        id="signin_username"
        placeholder="Username"
        errorMessage={$errors.username?.[0]}
        aria-invalid={$errors.username ? "true" : undefined}
        bind:value={$form.username}
        {...$constraints.username}
      />
      <Input
        id="signin_password"
        placeholder="Password"
        type="password"
        errorMessage={$errors.password?.[0]}
        aria-invalid={$errors.password ? "true" : undefined}
        bind:value={$form.password}
        {...$constraints.password}
      />
    </div>

    <div>
      <button type="submit" class="text-lg hover:underline">Continue</button>
      <ErrorMessage message={$message} />
    </div>
  </form>
</StickyFramework>
