<!-- TokenUsage.svelte -->
<script>
  // Token costs in USD per million tokens
  const tokenCosts = {
    'gpt-4o': {
      input: 2.50,
      output: 10.00
    },
    'o1-mini': {
      input: 1.10,
      output: 4.40
    },
    'gpt-4o-mini': {
      input: 0.15,
      output: 0.60
    },
  };

  const calculateCost = (tokens, type, model) => {
    // Default to gpt-4o costs if model not found in costs map
    const modelCosts = tokenCosts[model.toLowerCase()] || tokenCosts['gpt-4o'];
    const costPerMillion = modelCosts[type];
    return (tokens * costPerMillion) / 1_000_000;
  };
  
  let tokenUsage = new Map();
  export let className = '';

  export function updateTokenUsage(agent, usage) {
    const existing = tokenUsage.get(agent) || { 
      request_tokens: 0, 
      response_tokens: 0,
      model: null 
    };
    const updatedUsage = { ...existing };
    updatedUsage.request_tokens += usage.request_tokens;
    updatedUsage.response_tokens += usage.response_tokens;
    updatedUsage.model = usage.model || existing.model;
    tokenUsage.set(agent, updatedUsage);
    tokenUsage = new Map(tokenUsage);
  }

  // Calculate totals
  $: totalRequestTokens = [...tokenUsage.values()].reduce((sum, u) => sum + u.request_tokens, 0);
  $: totalResponseTokens = [...tokenUsage.values()].reduce((sum, u) => sum + u.response_tokens, 0);
  $: totalTokens = totalRequestTokens + totalResponseTokens;

  // Calculate total costs
  $: totalCost = [...tokenUsage].reduce((sum, [_, usage]) => {
    if (!usage.model) return sum;
    const inputCost = calculateCost(usage.request_tokens, 'input', usage.model);
    const outputCost = calculateCost(usage.response_tokens, 'output', usage.model);
    return sum + inputCost + outputCost;
  }, 0);
</script>

<div class="token-usage p-4 bg-gray-800 rounded-lg shadow-sm {className}">
  <h3 class="text-lg font-semibold mb-3">Token Usage</h3>
  <!-- Token Summary -->
  <div class="token-summary mb-4">
    <div class="grid grid-cols-4 gap-4 text-sm">
      <div><strong>Total Request Tokens:</strong> {totalRequestTokens}</div>
      <div><strong>Total Response Tokens:</strong> {totalResponseTokens}</div>
      <div><strong>Total Tokens:</strong> {totalTokens}</div>
      <div><strong>Total Cost:</strong> ${totalCost.toFixed(4)}</div>
    </div>
  </div>
  {#if tokenUsage.size > 0}
    <div class="space-y-3">
      {#each [...tokenUsage] as [agent, usage]}
        {@const inputCost = usage.model ? calculateCost(usage.request_tokens, 'input', usage.model) : 0}
        {@const outputCost = usage.model ? calculateCost(usage.response_tokens, 'output', usage.model) : 0}
        {@const totalAgentCost = inputCost + outputCost}
        <div class="bg-gray-50 dark:bg-gray-700 p-3 rounded">
          <h4 class="font-medium capitalize mb-1">{agent} {#if usage.model}({usage.model}){/if}</h4>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>Request tokens: {usage.request_tokens} (${inputCost.toFixed(4)})</div>
            <div>Response tokens: {usage.response_tokens} (${outputCost.toFixed(4)})</div>
            <div class="col-span-2">
              Total Tokens: {usage.request_tokens + usage.response_tokens}
              <span class="ml-2">Cost: ${totalAgentCost.toFixed(4)}</span>
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