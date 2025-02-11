<script>
  import { createEventDispatcher } from 'svelte';
  import { formState } from './stores.js';

  const dispatch = createEventDispatcher();

  export let orchestrationStarted = false;
  export let orchestrationFinished = false;

  $: if (!orchestrationStarted || orchestrationFinished) {
    // Re-enable form input when orchestration is not running
    formState.set($formState);
  }

  function startOrchestration() {
    dispatch('start', {
      type: "default",  // Changed from "init" to "default" to match backend expectation
      content: $formState.userRequest,
      config: {
        review: $formState.review,
        max_iterations: $formState.max_iterations,
        root_directory: $formState.rootDirectory
      }
    });
  }
</script>

<div class="mb-6">
  <label for="userRequest" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100 align-top">
    User Request:
  </label>
  <textarea
    id="userRequest"
    bind:value={$formState.userRequest}
    readonly={orchestrationStarted}
    rows="4"
    class="w-full p-2 border border-gray-300 dark:border-gray-600 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
    class:bg-gray-100={orchestrationStarted}
  ></textarea>

  <div class="mb-4">
    <label for="rootDirectory" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100">
      Working Directory:
    </label>
    <input
      id="rootDirectory"
      type="text"
      bind:value={$formState.rootDirectory}
      placeholder="."
      class="w-full p-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
    />
  </div>

  <div class="flex items-start mb-6 gap-4">
    <div class="flex items-center">
      <label for="review" class="block text-lg font-medium mb-2 text-gray-900 dark:text-gray-100 align-top">
        Enable Review:
      </label>
      <input
        id="review"
        type="checkbox"
        bind:checked={$formState.review}
        class="ml-2 leading-tight w-6 h-6"
      />
      <span class="ml-2 text-gray-700 dark:text-gray-300">Yes</span>
    </div>
    <div class="flex items-center">
      <label for="max_iterations" class="block text-lg font-medium mr-2 text-gray-900 dark:text-gray-100">
        Max Iterations:
      </label>
      <input
        id="max_iterations"
        type="number"
        bind:value={$formState.max_iterations}
        min="1"
        class="w-20 p-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
  {:else if !orchestrationFinished}
    <div class="text-sm text-gray-600 dark:text-gray-400">
      Orchestration in progress...
    </div>
  {/if}
</div>