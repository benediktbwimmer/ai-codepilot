from pydantic_ai.result import RunResult

async def send_usage(comm, response: RunResult, agent_name: str):
    """Send token usage information to the frontend if available.
    
    Args:
        comm: Communication channel to send messages
        response: Response object that might have usage information
        agent_name: Name of the agent that made the request
    """
    if comm and hasattr(response, 'usage'):
        usage = response.usage()
        if usage:
            await comm.send("token_usage", {
                "agent": agent_name,
                "request_tokens": usage.request_tokens,
                "response_tokens": usage.response_tokens
            })