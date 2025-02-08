<script>
  import { createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  
  const dispatch = createEventDispatcher();
  
  export let questionMessage = "";
  export let questionAnswer = "";

  function sendAnswer() {
    dispatch('answer', { answer: questionAnswer });
    questionAnswer = "";
  }

  function parseMarkdown(text) {
    marked.setOptions({
      gfm: true,
      breaks: true
    });
    return marked.parse(text);
  }
</script>

<div class="mb-6">
  <div class="mb-4 text-lg text-gray-900 dark:text-gray-100">
    {@html parseMarkdown(questionMessage)}
  </div>
  <div class="flex space-x-4">
    <input
      type="text"
      bind:value={questionAnswer}
      class="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
    />
    <button
      on:click={sendAnswer}
      class="px-4 py-2 bg-blue-300 text-white rounded hover:bg-blue-400 focus:outline-none dark:bg-blue-400 dark:hover:bg-blue-500"
    >
      Send Answer
    </button>
  </div>
</div>