<script>
  import { createEventDispatcher } from 'svelte';
  import { marked } from 'marked';
  
  const dispatch = createEventDispatcher();
  
  export let questionMessage = "";
  export let questionAnswer = "";

  function sendAnswer() {
    if (questionAnswer.trim()) {
      dispatch('answer', { answer: questionAnswer });
      questionAnswer = "";
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendAnswer();
    }
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
      on:keydown={handleKeydown}
      placeholder="Type your answer and press Enter"
      class="flex-1 p-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
    />
    <button
      on:click={sendAnswer}
      disabled={!questionAnswer.trim()}
      class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed dark:bg-blue-600 dark:hover:bg-blue-700"
    >
      Send Answer
    </button>
  </div>
</div>