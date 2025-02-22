<script>
  import { onMount } from 'svelte';
  import loader from '@monaco-editor/loader';

  export let diffText = '';
  export let language = 'plaintext';
  let container;
  let editor;
  let monacoInstance;

  onMount(() => {
    loader.init().then(monaco => {
      monacoInstance = monaco;
      if (container) {
        editor = monaco.editor.createDiffEditor(container, {
          automaticLayout: true,
          readOnly: true,
          theme: 'vs-dark',
          renderSideBySide: true,
          ignoreTrimWhitespace: false
        });

        if (diffText) {
          updateDiff(diffText);
        }
      }
    });

    return () => {
      if (editor) {
        editor.dispose();
      }
    };
  });

  $: if (editor && diffText && monacoInstance) {
    updateDiff(diffText);
  }

  function updateDiff(diffText) {
    try {
      const parsedDiff = parsePatch(diffText);
      if (diffText) {
        const originalModel = monacoInstance.editor.createModel(parsedDiff.original, language);
        const modifiedModel = monacoInstance.editor.createModel(parsedDiff.modified, language);
        editor.setModel({
          original: originalModel,
          modified: modifiedModel
        });
      }
    } catch (e) {
      console.error('Error parsing diff:', e);
      // Optionally, set an error state or provide user feedback here to handle the error gracefully.
    }
  }

  function parsePatch(diffText) {
    if (!diffText) return null;
    
    const lines = diffText.split('\n');
    let original = [];
    let modified = [];
    
    for (const line of lines) {
      if (line.startsWith('-')) {
        original.push(line.slice(1));
      } else if (line.startsWith('+')) {
        modified.push(line.slice(1));
      } else {
        original.push(line);
        modified.push(line);
      }
    }
    
    return {
      original: original.join('\n'),
      modified: modified.join('\n')
    };
  }

</script>

<div 
  class="diff-container bg-white dark:bg-gray-800 rounded shadow mb-6" 
  bind:this={container}
  style="height: 600px; width: 100%;"
></div>

<style>
  .diff-container {
    min-height: 400px;
  }
</style>