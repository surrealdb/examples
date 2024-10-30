<script lang="ts">
  type Props = {
    message?: string;
  };

  let { message }: Props = $props();
</script>

<p class="mb-1 text-sm text-red-700">{message}</p>
