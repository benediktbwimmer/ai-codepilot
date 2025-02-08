<script>
  import { createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  
  const dispatch = createEventDispatcher();
  
  export let confirmationMessage = "";

  function sendConfirmation(response) {
    dispatch('confirm', { response });
  }

  function parseMarkdown(text) {
    marked.setOptions({
      gfm: true,
      breaks: true
    });
    return marked.parse(text);
  }
</script>

<div class="p-4 bg-white dark:bg-gray-800 rounded shadow mb-6">
  <div class="mb-4 text-lg text-gray-900 dark:text-white">
    {@html parseMarkdown(confirmationMessage)}
  </div>
  <div class="flex space-x-4">
    <button
      on:click={() => sendConfirmation("y")}
      class="px-4 py-2 bg-green-300 text-white rounded hover:bg-green-400 focus:outline-none dark:bg-green-400 dark:hover:bg-green-500"
    >
      Yes
    </button>
    <button
      on:click={() => sendConfirmation("f")}
      class="px-4 py-2 bg-blue-300 text-white rounded hover:bg-blue-400 focus:outline-none dark:bg-blue-400 dark:hover:bg-blue-500"
    >
      Feedback
    </button>
    <button
      on:click={() => sendConfirmation("n")}
      class="px-4 py-2 bg-red-300 text-white rounded hover:bg-red-400 focus:outline-none dark:bg-red-400 dark:hover:bg-red-500"
    >
      No
    </button>
  </div>
</div>