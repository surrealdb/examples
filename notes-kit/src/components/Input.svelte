<script lang="ts">
  import { cn } from "$lib/utils";
  import type { HTMLInputAttributes } from "svelte/elements";
  import type { InputConstraint } from "sveltekit-superforms";
  import ErrorMessage from "./ErrorMessage.svelte";

  type Props = HTMLInputAttributes & {
    errorMessage?: string;
    constraints?: InputConstraint;
  };

  const className = "";

  let {
    id,
    type,
    value = $bindable(""),
    placeholder,
    errorMessage,
    constraints,
    ...rest
  }: Props = $props();
</script>

<div class="relative w-full">
  <input
    {id}
    {type}
    class={cn(
      "peer w-full rounded-md bg-transparent pt-3 text-lg text-white outline-none placeholder:text-white placeholder:opacity-80",
      className
    )}
    placeholder=""
    bind:value
    {...constraints}
    {...rest}
  />
  <label
    for={id}
    class="pointer-events-none absolute left-0 top-1 z-10 origin-[0] -translate-y-3 scale-50 transform text-white opacity-50 duration-200 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:scale-100 peer-placeholder-shown:opacity-80 peer-focus:-translate-y-3 peer-focus:scale-50 peer-focus:opacity-80"
  >
    {placeholder}
  </label>
  <ErrorMessage message={errorMessage} />
</div>
