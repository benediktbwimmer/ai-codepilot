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
  let waitingForConfirmation = false;
  let confirmationMessage = "";
  let waitingForQuestion = false;
  let questionMessage = "";
  let orchestrationStarted = false;
  let orchestrationFinished = false;
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
      }
    };
  });

  function handleStart(event) {
    orchestrationStarted = true;
    ws = new WebSocket(`ws://localhost:8000/ws`);
    ws.onopen = () => {
      ws.send(JSON.stringify(event.detail));
    };
    ws.onmessage = handleWebSocketMessage;
    ws.onclose = () => {
      console.log("WebSocket closed");
      orchestrationStarted = false;
    };
  }

  function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    if (data.type === "confirmation") {
      waitingForConfirmation = true;
      confirmationMessage = data.content;
    } else if (data.type === "question") {
      waitingForQuestion = true;
      questionMessage = data.content;
    } else if (data.type === "diff") {
      messagesState.update(state => ({ ...state, currentDiff: data.content }));
    } else if (data.type === "completed") {
      orchestrationFinished = true;
      orchestrationStarted = false;
    } else if (data.type === "token_usage") {
      tokenUsageComponent.updateTokenUsage(data.content.agent, {
        request_tokens: data.content.request_tokens,
        response_tokens: data.content.response_tokens
      });
    } else {
      messagesState.update(state => ({
        ...state,
        messages: [...state.messages, { type: data.type, content: data.content }]
      }));
    }
  }

  function handleConfirmation(event) {
    waitingForConfirmation = false;
    ws.send(JSON.stringify({ type: "confirmation", content: event.detail.response }));
  }

  function handleQuestionAnswer(event) {
    waitingForQuestion = false;
    ws.send(JSON.stringify({ type: "question_answer", content: event.detail.answer }));
  }
</script>

<main class="min-h-screen bg-gray-100 dark:bg-gray-900 dark:text-white transition-colors duration-200">
  <div class="flex h-screen">
    <!-- Left Panel -->
    <div class="w-1/2 p-6 overflow-y-auto border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <Header />
      
      <UserInput
        {orchestrationStarted}
        {orchestrationFinished}
        on:start={handleStart}
      />

      {#if orchestrationFinished}
        <div class="mt-4 p-4 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg flex items-center shadow-sm">
          <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="font-medium">Orchestration completed successfully!</span>
        </div>
      {/if}

      <div class="conditional-wrappers">
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

      <DiffViewer diffText={$messagesState.currentDiff} />

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