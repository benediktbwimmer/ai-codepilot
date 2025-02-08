<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let userRequest = "";
  export let orchestrationStarted = false;
  
  let review = true;
  let max_iterations = 2;

  function startOrchestration() {
    dispatch('start', { userRequest, review, max_iterations });
  }
</script>

<div class="mb-6">
  <label for="userRequest" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100 align-top">
    User Request:
  </label>
  <textarea
    id="userRequest"
    bind:value={userRequest}
    readonly={orchestrationStarted}
    rows="4"
    class="w-full p-2 border border-gray-300 dark:border-gray-600 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
    class:bg-gray-100={orchestrationStarted}
  ></textarea>
  
  <div class="flex items-start mb-6">
    <div class="mr-4">
      <label for="review" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100 align-top">
        Enable Review:
      </label>
      <input
        id="review"
        type="checkbox"
        bind:checked={review}
        class="mr-2 leading-tight w-6 h-6"
      />
      <span class="text-gray-700 dark:text-gray-300">Yes</span>
    </div>
    <div>
      <label for="max_iterations" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100 align-top">
        Max Iterations:
      </label>
      <input
        id="max_iterations"
        type="number"
        bind:value={max_iterations}
        min="1"
        class="w-20 p-2 border border-gray-300 dark:border-gray-600 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
      />
    </div>
  </div>

  {#if !orchestrationStarted}
    <button
      on:click={startOrchestration}
      class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none disabled:opacity-50 dark:bg-green-600 dark:hover:bg-green-700"
    >
      Start Orchestration
    </button>
  {:else}
    <div class="text-sm text-gray-600 dark:text-gray-400">
      Orchestration in progress...
    </div>
  {/if}
</div>