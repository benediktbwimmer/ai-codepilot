<script>
  import { onMount } from "svelte";
  import Header from "./lib/Header.svelte";
  import UserInput from "./lib/UserInput.svelte";
  import QuestionPrompt from "./lib/QuestionPrompt.svelte";
  import ConfirmationDialog from "./lib/ConfirmationDialog.svelte";
  import DiffViewer from "./lib/DiffViewer.svelte";
  import LogViewer from "./lib/LogViewer.svelte";

  let ws = null;
  let userRequest = "";
  let messages = [];
  let waitingForConfirmation = false;
  let confirmationMessage = "";
  let waitingForQuestion = false;
  let questionMessage = "";
  let orchestrationStarted = false;
  let currentDiff = "";
  let orchestrationFinished = false;


  function handleStart(event) {
    userRequest = event.detail.userRequest;
    orchestrationStarted = true;
    ws = new WebSocket(`ws://localhost:8000/ws`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "init", content: userRequest }));
    };
    ws.onmessage = handleWebSocketMessage;
    ws.onclose = () => {
      console.log("WebSocket closed");
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
      currentDiff = data.content;
    } else if (data.type === "completed") {
        orchestrationFinished = true;
    } else {
      messages = [...messages, { type: data.type, content: data.content }];
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
    <div class="w-1/2 p-6 overflow-y-auto border-r border-gray-200 dark:border-gray-700">
      <Header />
      
      <UserInput
        {userRequest}
        {orchestrationStarted}
        on:start={handleStart}
      />

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

      <DiffViewer diffText={currentDiff} />

      {#if orchestrationFinished}
        <div class="mt-4 p-4 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg flex items-center shadow-sm">
          <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <span class="font-medium">Orchestration completed successfully!</span>
        </div>
      {/if}
    </div>

    <!-- Right Panel - Logs -->
    <div class="w-1/2">
      <LogViewer {messages} />
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
