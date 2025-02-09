<!-- TokenUsage.svelte -->
<script>
  let tokenUsage = new Map();
  export let className = '';

  export function updateTokenUsage(agent, usage) {
    const existing = tokenUsage.get(agent) || { request_tokens: 0, response_tokens: 0 };
    const updatedUsage = { ...existing };
    updatedUsage.request_tokens += usage.request_tokens;
    updatedUsage.response_tokens += usage.response_tokens;
    tokenUsage.set(agent, updatedUsage);
  }

  // Calculate totals
  $: totalRequestTokens = [...tokenUsage.values()].reduce((sum, u) => sum + u.request_tokens, 0);
  $: totalResponseTokens = [...tokenUsage.values()].reduce((sum, u) => sum + u.response_tokens, 0);
  $: totalTokens = totalRequestTokens + totalResponseTokens;
</script>

<div class="token-usage p-4 bg-gray-800 rounded-lg shadow-sm {className}">
  <h3 class="text-lg font-semibold mb-3">Token Usage</h3>
  <!-- Token Summary -->
  <div class="token-summary mb-4">
    <div class="grid grid-cols-3 gap-4 text-sm">
      <div><strong>Total Request Tokens:</strong> {totalRequestTokens}</div>
      <div><strong>Total Response Tokens:</strong> {totalResponseTokens}</div>
      <div><strong>Total Tokens:</strong> {totalTokens}</div>
    </div>
  </div>
  {#if tokenUsage.size > 0}
    <div class="space-y-3">
      {#each [...tokenUsage] as [agent, usage]}
        <div class="bg-gray-50 dark:bg-gray-700 p-3 rounded">
          <h4 class="font-medium capitalize mb-1">{agent}</h4>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>Request tokens: {usage.request_tokens}</div>
            <div>Response tokens: {usage.response_tokens}</div>
            <div class="col-span-2">
              Total: {usage.request_tokens + usage.response_tokens}
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-gray-500 dark:text-gray-400">No token usage data yet</p>
  {/if}
</div>

<style>
  .token-usage {
    max-width: 100%;
    margin: 1rem 0;
  }
  .token-summary {
    background-color: #374151;
    padding: 1rem;
    border-radius: 0.5rem;
  }
</style>