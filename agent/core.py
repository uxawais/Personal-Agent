import json
import logging
from agent.config import get_settings
from agent.conversation import Conversation
from agent.personality import get_effective_system_prompt, get_personality
from models.router import ModelRouter
from tools.registry import get_tool_schemas, execute_tool

logger = logging.getLogger(__name__)


class AgentCore:
    def __init__(self, redis_client, model_router: ModelRouter):
        self.redis = redis_client
        self.model_router = model_router

    async def process_message(
        self,
        user_message: str,
        conversation_id: str | None = None,
        channel: str = "web",
        user_id: str = "default",
    ) -> str:
        conv = Conversation(self.redis, conversation_id or f"{channel}:{user_id}")
        await conv.add_message("user", user_message, {"channel": channel})

        history = await conv.get_messages_for_model()
        tools = get_tool_schemas()

        messages = [{"role": "system", "content": get_effective_system_prompt()}] + history

        max_iterations = 5
        for iteration in range(max_iterations):
            response = await self.model_router.complete(
                messages=messages,
                tools=tools if tools else None,
                max_tokens=get_personality().max_tokens,
                temperature=get_personality().temperature,
            )

            if response.tool_calls:
                tool_calls_formatted = []
                for tc in response.tool_calls:
                    tool_calls_formatted.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    })
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": tool_calls_formatted,
                })

                for tool_call in response.tool_calls:
                    logger.info(f"Executing tool: {tool_call.name}({tool_call.arguments})")
                    try:
                        result = await execute_tool(tool_call.name, tool_call.arguments)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        })
                    except Exception as e:
                        logger.error(f"Tool {tool_call.name} failed: {e}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Error: {str(e)}",
                        })
                continue

            final_text = response.content or "I'm sorry, I couldn't generate a response."
            await conv.add_message("assistant", final_text, {"channel": channel})
            return final_text

        fallback = "I reached the maximum number of tool iterations. Here's what I have so far based on our conversation."
        await conv.add_message("assistant", fallback, {"channel": channel})
        return fallback
