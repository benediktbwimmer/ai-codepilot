<script>
  import { onMount } from "svelte";
  import { formState, messagesState } from "./lib/stores.js";
  import Header from "./lib/Header.svelte";
  import UserInput from "./lib/UserInput.svelte";
  import QuestionPrompt from "./lib/QuestionPrompt.svelte";
  import ConfirmationDialog from "./lib/ConfirmationDialog.svelte";
  import DiffViewer from "./lib/DiffViewer.svelte";
  import LogViewer from "./lib/LogViewer.svelte";
  import TokenUsage from "./lib/TokenUsage.svelte";

  let ws = null;
  let wsConnected = false;
  let waitingForConfirmation = false;
  let confirmationMessage = "";
  let waitingForQuestion = false;
  let questionMessage = "";
  let orchestrationStarted = false;
  let orchestrationFinished = false;
  let orchestrationStopped = false;
  let tokenUsageComponent;

  onMount(() => {
    // Initialize stores if they're empty
    formState.update(state => ({
      userRequest: state.userRequest || '',
      review: state.review ?? true,
      max_iterations: state.max_iterations ?? 2,
      rootDirectory: state.rootDirectory || '.'
    }));

    messagesState.update(state => ({
      messages: state.messages || [],
      currentDiff: state.currentDiff || ''
    }));

    // Clear messages when starting fresh
    if (!orchestrationStarted) {
      messagesState.set({
        messages: [],
        currentDiff: ''
      });
    }

    return () => {
      if (ws) {
        ws.close();
        ws = null;
      }
    };
  });

  function handleStart(event) {
    if (ws) {
      ws.close();
    }
    
    // Reset all states
    orchestrationStarted = true;
    orchestrationFinished = false;
    orchestrationStopped = false;
    waitingForQuestion = false;
    waitingForConfirmation = false;
    questionMessage = "";
    confirmationMessage = "";
    
    // Clear messages and diffs
    messagesState.set({
      messages: [],
      currentDiff: '',
      language: 'plaintext'
    });
    
    ws = new WebSocket(`ws://localhost:8000/ws`);
    
    ws.onopen = () => {
      wsConnected = true;
      ws.send(JSON.stringify({ type: "default", ...event.detail }));
    };
    
    ws.onmessage = handleWebSocketMessage;
    
    ws.onclose = () => {
      console.log("WebSocket closed");
      wsConnected = false;
      orchestrationStarted = false;
      ws = null;
    };
    
    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      orchestrationStarted = false;
      wsConnected = false;
    };
  }

  function handleStop() {
    if (ws && wsConnected && orchestrationStarted && !orchestrationFinished) {
      ws.send(JSON.stringify({ type: "stop", content: "stop" }));
      orchestrationStopped = true;
      // Add stop message to logs
      messagesState.update(state => ({
        ...state,
        messages: [...state.messages, { type: "log", content: "Orchestration stopped by user." }]
      }));
    }
  }

  function getLanguageFromFilename(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'ts': 'typescript',
      'py': 'python',
      'html': 'html',
      'css': 'css',
      'svelte': 'html',
      'json': 'json',
      'md': 'markdown'
    };
    return languageMap[ext] || 'plaintext';
  }

  function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    console.log("Received WebSocket message:", data);
    
    if (data.type === "confirmation") {
      waitingForConfirmation = true;
      confirmationMessage = data.content;
    } else if (data.type === "question") {
      waitingForQuestion = true;
      questionMessage = data.content;
    } else if (data.type === "diff") {
      const diffLines = data.content.split('\n');
      const filenameLine = diffLines[0];
      const filename = filenameLine.split(' ')[1] || '';
      const language = getLanguageFromFilename(filename);
      messagesState.update(state => ({ ...state, currentDiff: data.content, language }));
    } else if (data.type === "completed" || data.type === "error") {
      resetOrchestrationState();
      // Add success/error message to logs
      messagesState.update(state => ({
        ...state,
        messages: [...state.messages, { type: data.type, content: data.content }]
      }));
    } else if (data.type === "token_usage") {
      tokenUsageComponent?.updateTokenUsage(data.content.agent, {
        request_tokens: data.content.request_tokens,
        response_tokens: data.content.response_tokens,
        model: data.content.model
      });
    } else if (data.type === "log" && data.content.includes("cancelled by user")) {
      // Set orchestrationStopped when receiving cancellation message
      orchestrationStopped = true;
      messagesState.update(state => ({
        ...state,
        messages: [...state.messages, { type: data.type, content: data.content }]
      }));
      resetOrchestrationState();
    } else {
      messagesState.update(state => ({
        ...state,
        messages: [...state.messages, { type: data.type, content: data.content }]
      }));
    }
  }

  function resetOrchestrationState() {
    // Reset all UI states
    orchestrationFinished = true;
    orchestrationStarted = false;
    waitingForQuestion = false;
    waitingForConfirmation = false;
    questionMessage = "";
    confirmationMessage = "";
    
    // Reset WebSocket state
    wsConnected = false;
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  function handleConfirmation(event) {
    if (ws && wsConnected) {
      waitingForConfirmation = false;
      ws.send(JSON.stringify({ type: "confirmation", content: event.detail.response }));
    }
  }

  function handleQuestionAnswer(event) {
    if (ws && wsConnected) {
      waitingForQuestion = false;
      // Change the message type to match what the backend expects
      ws.send(JSON.stringify({ type: "question", content: event.detail.answer }));
    }
  }
</script>

<main class="min-h-screen bg-gray-100 dark:bg-gray-900 dark:text-white transition-colors duration-200">
  <div class="flex h-screen">
    <!-- Left Panel -->
    <div class="w-1/2 p-6 overflow-y-auto border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <Header />
      
      <div class="flex flex-col space-y-4">
        <UserInput
          {orchestrationStarted}
          {orchestrationFinished}
          on:start={handleStart}
        />

        {#if orchestrationStarted && !orchestrationFinished}
          <div class="flex justify-end">
            <button 
              class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors duration-200"
              on:click={handleStop}
            >
              Stop Orchestration
            </button>
          </div>
        {/if}

        {#if orchestrationFinished}
          <div class="p-4 {orchestrationStopped ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300' : 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'} rounded-lg flex items-center shadow-sm">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {#if orchestrationStopped}
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              {:else}
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              {/if}
            </svg>
            <span class="font-medium">
              {#if orchestrationStopped}
                Orchestration stopped by user
              {:else}
                Orchestration completed successfully!
              {/if}
            </span>
          </div>
        {/if}
      </div>

      <div class="conditional-wrappers mt-4">
        {#if waitingForQuestion}
          <QuestionPrompt
            {questionMessage}
            on:answer={handleQuestionAnswer}
          />
        {/if}
        {#if waitingForConfirmation}
          <ConfirmationDialog
            {confirmationMessage}
            on:confirm={handleConfirmation}
          />
        {/if}
      </div>

      <DiffViewer diffText={$messagesState.currentDiff} language={$messagesState.language} />

      <div class="mt-auto pt-4">
        <TokenUsage bind:this={tokenUsageComponent} className="bg-gray-800 text-white p-4 rounded" />
      </div>
    </div>

    <!-- Right Panel - Logs -->
    <div class="w-1/2">
      <LogViewer messages={$messagesState.messages} />
    </div>
  </div>
</main>

<style>
  /* Component-specific styles only */
  :global(.d2h-wrapper) {
    margin: 0;
    padding: 0;
  }
</style>