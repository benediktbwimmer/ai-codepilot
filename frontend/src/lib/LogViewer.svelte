<script>
  import { marked } from 'marked';
  import { onMount, afterUpdate } from 'svelte';

  export let messages = [];
  let logsContainer;

  afterUpdate(() => {
    if (logsContainer) {
      logsContainer.scrollTop = logsContainer.scrollHeight;
    }
  });

  function parseMarkdown(text) {
    marked.setOptions({
      gfm: true,
      breaks: true
    });
    return marked.parse(text);
  }

  $: logClass = `h-screen overflow-y-auto bg-gray-50 dark:bg-gray-800 p-4 font-mono text-sm`;
</script>

<div class={logClass} bind:this={logsContainer}>
  {#each messages as message}
    {#if message.type === 'log'}
      <div class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap mb-2">
        {message.content}
      </div>
    {:else if message.type === 'error'}
      <div class="text-red-600 dark:text-red-400 whitespace-pre-wrap mb-2">
        {message.content}
      </div>
    {/if}
  {/each}
</div>

<style>
  .messages {
    height: calc(100vh - 2rem);
    overflow-y: auto;
    scroll-behavior: smooth;
    padding: 1rem;
  }
</style>