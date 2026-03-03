"""
Simulation manager for handling model interactions and tool execution.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any
import os
from pathlib import Path

# Import API clients
try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

try:
    import anthropic
    from anthropic import Anthropic
except ImportError:
    anthropic = None
    Anthropic = None


class SimulationManager:
    """Manages interaction between simulation and language models."""

    def __init__(self, simulation, model: str, max_retries: int = 3,
                 run_id: int = 1, log_dir: Optional[str] = None,
                 system_message: Optional[Dict] = None, thinking_mode: bool = False):
        self.simulation = simulation
        self.model = model
        self.max_retries = max_retries
        self.run_id = run_id
        self.logger = logging.getLogger(__name__)
        self.system_message = system_message
        self.thinking_mode = thinking_mode

        # Message history
        self.messages = []

        # Setup trajectory logging
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path(f"logs_{model}")
        self.log_dir.mkdir(exist_ok=True)

        self.log_file = self.log_dir / f"run_{run_id}_trajectory.txt"
        self.init_log_file()

        # Initialize API client
        self.client = self._init_client()

        # Get tools
        self.tools = simulation.get_tools()

    def init_log_file(self):
        """Initialize the trajectory log file."""
        with open(self.log_file, 'w') as f:
            f.write(f"ER Simulation Trajectory Log\n")
            f.write(f"Run ID: {self.run_id}\n")
            f.write(f"Model: {self.model}\n")
            f.write("=" * 80 + "\n\n")

    def log_timestep_header(self, timestep: int):
        """Log the header for a new timestep."""
        with open(self.log_file, 'a') as f:
            f.write(f"\nTimestep: {timestep}\n")
            f.write("-" * 80 + "\n")

    def log_user_message(self, message: str):
        """Log a user message to the trajectory file."""
        with open(self.log_file, 'a') as f:
            f.write("USER MESSAGE:\n")
            f.write(message)
            f.write("\n\n")

    def log_assistant_response(self, response: Any):
        """Log assistant response to the trajectory file."""
        with open(self.log_file, 'a') as f:
            f.write("ASSISTANT RESPONSE:\n")

            # Extract content based on model type
            if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
                if hasattr(response, 'choices') and response.choices:
                    message = response.choices[0].message
                    content = message.content if hasattr(message, 'content') else ""
                    if content:
                        f.write(f"Content: {content}\n")

                    # Log tool calls
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        f.write("\nTOOL CALLS:\n")
                        for tool_call in message.tool_calls:
                            f.write(f"  - Function: {tool_call.function.name}\n")
                            f.write(f"    Arguments: {tool_call.function.arguments}\n")

            elif "claude" in self.model:
                if hasattr(response, 'content') and response.content:
                    for content_block in response.content:
                        if hasattr(content_block, 'text'):
                            f.write(f"Content: {content_block.text}\n")
                        elif hasattr(content_block, 'type') and content_block.type == 'tool_use':
                            f.write(f"\nTOOL CALL:\n")
                            f.write(f"  - Function: {content_block.name}\n")
                            f.write(f"    Arguments: {json.dumps(content_block.input)}\n")

            f.write("\n")

    def log_tool_results(self, tool_results: List[Dict]):
        """Log tool execution results (without metrics visible to agent)."""
        with open(self.log_file, 'a') as f:
            f.write("TOOL RESULTS:\n")
            for result in tool_results:
                f.write(f"  Tool: {result.get('tool_name', 'unknown')}\n")
                f.write(f"  Success: {result.get('result', {}).get('success', False)}\n")
                if 'message' in result.get('result', {}):
                    f.write(f"  Message: {result['result']['message']}\n")
                if 'default_placements' in result.get('result', {}):
                    defaults = result['result']['default_placements']
                    if defaults:
                        f.write(f"  Default Placements (end of queue): {', '.join(defaults)}\n")
                # Note: Metrics are tracked internally but not shown in logs
            f.write("\n")

    def log_queue_state(self):
        """Log the current queue state."""
        with open(self.log_file, 'a') as f:
            f.write("QUEUE STATE:\n")
            f.write(f"  Queue Length: {len(self.simulation.queue)}\n")
            f.write(f"  New Patients: {len(self.simulation.new_patients)}\n")

            if self.simulation.queue:
                f.write("  Current Queue Order:\n")
                for i, patient in enumerate(self.simulation.queue[:10]):  # Show first 10
                    f.write(f"    {i+1}. {patient.first_name} {patient.last_name} "
                           f"(Insured: {patient.insured}, Critical: {patient.is_critical})\n")
                if len(self.simulation.queue) > 10:
                    f.write(f"    ... and {len(self.simulation.queue) - 10} more patients\n")
            f.write("\n")

    def _init_client(self):
        """Initialize the appropriate API client."""
        if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
            if OpenAI is None:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable not set")
            return OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

        elif "claude" in self.model:
            if Anthropic is None:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            return Anthropic(api_key=api_key)

        else:
            raise ValueError(f"Unsupported model: {self.model}")

    def run_timestep(self, user_message: str, timestep: int) -> Dict:
        """Run a single timestep interaction with the model."""
        # Log timestep header
        self.log_timestep_header(timestep)

        # Log user message
        self.log_user_message(user_message)

        # Add user message to history
        self.messages.append({"role": "user", "content": user_message})

        i = 0
        while not self._timestep_finished():

            # Get model response
            response = self._get_model_response()

            # Log assistant response
            self.log_assistant_response(response)

            # Process tool calls if any
            tool_results = []
            if self._has_tool_calls(response):
                tool_results = self._execute_tool_calls(response)
                # Log tool results
                self.log_tool_results(tool_results)
                # Add tool results to message history
                self._add_tool_results(tool_results)

            i += 1

            if i == 10:
                self._force_finish_timestep()

        # Ensure timestep is finished
        # if not self._timestep_finished():
        #     self._force_finish_timestep()

        # ALWAYS calculate and save metrics at the end of each timestep
        # (even if finish_timestep was not called because all patients were placed)
        if not self.simulation.timestep_metrics or len(self.simulation.timestep_metrics) < self.simulation.current_timestep:
            metrics = self.simulation.calculate_timestep_metrics()
            self.simulation.timestep_metrics.append(metrics)
            self.logger.info(f"Calculated metrics for timestep {self.simulation.current_timestep}")

        # Log final queue state
        self.log_queue_state()

        return {
            'response': response,
            'timestep': timestep,
            'queue_length': len(self.simulation.queue),
            'tool_results': tool_results
        }

    def _get_model_response(self) -> Any:
        """Get response from the language model."""
        for attempt in range(self.max_retries):
            try:
                if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
                    return self._get_openai_response()
                elif "claude" in self.model:
                    return self._get_anthropic_response()
            except Exception as e:
                self.logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def _get_openai_response(self):
        """Get response from OpenAI model."""
        # Prepare messages with system prompt
        messages_with_system = []
        if self.system_message:
            messages_with_system.append(self.system_message)
        messages_with_system.extend(self.messages)

        # Determine which parameters to use based on model
        # Newer models (gpt-4o, gpt-4o-mini, gpt-5, etc.) use max_completion_tokens
        # Some models (o1, gpt-5-mini) don't support custom temperature
        api_params = {
            'model': self.model,
            'messages': messages_with_system,
            'tools': self.tools if self.tools else None,
            # 'tool_choice': "auto"
        }

        # Add extra_body with reasoning only when thinking_mode flag is set
        # This is controlled via the --thinking command line flag
        extra_body = {}
        if self.thinking_mode:
            extra_body['reasoning'] = {'enabled': True}
        
        if extra_body:
            api_params['extra_body'] = extra_body

        # Token parameter
        # if any(model_name in self.model.lower() for model_name in ['gpt-4o', 'gpt-5', 'o1']):
        #     api_params['max_completion_tokens'] = 2000
        # else:
        #     api_params['max_tokens'] = 2000

        # Temperature parameter (some models only support default temperature=1)
        # o1 and gpt-5-mini models don't support custom temperature
        # if not any(model_name in self.model.lower() for model_name in ['o1', 'gpt-5-mini']):
        #     api_params['temperature'] = 0.7

        response = self.client.chat.completions.create(**api_params)

        if not response or not response.choices:
            return None

        # Add assistant message to history - convert to plain dict to avoid serialization issues
        msg = response.choices[0].message
        msg_dict = {
            "role": msg.role,
            "content": msg.content or ""
        }
        # Preserve tool_calls if present
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        self.messages.append(msg_dict)

        return response

    def _add_prompt_caching(self, messages: List[Dict], tools: List[Dict]) -> tuple:
        """Add prompt caching to messages and tools.
        
        Caches the last 2 TEXT-type user messages to create conversation checkpoints.
        Tool result messages are skipped as they don't support caching.
        This allows the API to reuse cached content for the conversation history.
        """
        import copy
        result = []
        text_user_turns_cached = 0
        
        # Deep copy tools and add cache_control to the last tool
        if tools:
            tools = copy.deepcopy(tools)
            tools[-1]["cache_control"] = {"type": "ephemeral"}
        
        # Process messages in reverse to find last 2 TEXT-type user messages
        for turn in reversed(messages):
            turn = copy.deepcopy(turn)  # Don't modify original
            role = turn.get("role")
            
            if role == "user" and text_user_turns_cached < 2:
                content = turn.get("content")
                
                # Check if this is a text message (string) or tool_result message (list with tool_result type)
                is_tool_result_msg = False
                if isinstance(content, list) and len(content) > 0:
                    # Check if any block is a tool_result
                    is_tool_result_msg = any(
                        isinstance(block, dict) and block.get("type") == "tool_result"
                        for block in content
                    )
                
                # Only add cache_control to text-type messages, not tool_result messages
                if not is_tool_result_msg:
                    if isinstance(content, str):
                        turn["content"] = [{"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}]
                    elif isinstance(content, list) and len(content) > 0:
                        # Find the last text block and add cache_control
                        for i in range(len(content) - 1, -1, -1):
                            if isinstance(content[i], dict) and content[i].get("type") == "text":
                                content[i]["cache_control"] = {"type": "ephemeral"}
                                break
                    text_user_turns_cached += 1
                
                result.append(turn)
            else:
                result.append(turn)
        
        return list(reversed(result)), tools

    def _get_anthropic_response(self):
        """Get response from Anthropic model."""
        import copy
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        for msg in self.messages:
            if msg['role'] == 'system':
                continue  # Handle system messages separately
            anthropic_messages.append({
                'role': msg['role'],
                'content': copy.deepcopy(msg['content'])
            })

        # Extract system message content with caching enabled
        system_content = None
        if self.system_message and 'content' in self.system_message:
            system_content = [
                {
                    "type": "text",
                    "text": self.system_message['content'],
                    "cache_control": {"type": "ephemeral"}
                }
            ]

        # Apply multi-turn prompt caching (caches last 2 user messages + last tool)
        cached_messages, cached_tools = self._add_prompt_caching(
            anthropic_messages, 
            copy.deepcopy(self.tools) if self.tools else None
        )

        response = self.client.messages.create(
            model=self.model,
            messages=cached_messages,
            system=system_content,  # Claude uses system parameter
            tools=cached_tools,
            temperature=0.7,
            max_tokens=2000
        )

        # Log cache statistics
        usage = response.usage
        cache_write = getattr(usage, 'cache_creation_input_tokens', 0) or 0
        cache_read = getattr(usage, 'cache_read_input_tokens', 0) or 0
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        self.logger.info(f"Tokens - Cache write: {cache_write} | Cache read: {cache_read} | Input: {input_tokens} | Output: {output_tokens}")

        # Add assistant message to history - must preserve tool_use blocks!
        # Convert SDK objects to plain dicts to avoid serialization issues
        content_dicts = []
        for block in response.content:
            if hasattr(block, 'type'):
                if block.type == 'text':
                    content_dicts.append({"type": "text", "text": block.text})
                elif block.type == 'tool_use':
                    content_dicts.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
        
        self.messages.append({
            'role': 'assistant',
            'content': content_dicts if content_dicts else ""
        })

        return response

    def _has_tool_calls(self, response) -> bool:
        """Check if response contains tool calls."""
        if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
            return (hasattr(response.choices[0].message, 'tool_calls') and
                   response.choices[0].message.tool_calls)
        elif "claude" in self.model:
            return (hasattr(response, 'content') and
                   any(hasattr(c, 'type') and c.type == 'tool_use'
                       for c in response.content))
        return False

    def _execute_tool_calls(self, response) -> List[Dict]:
        """Execute tool calls from model response."""
        tool_results = []

        if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
            for tool_call in response.choices[0].message.tool_calls:

                raw_args = tool_call.function.arguments
                if raw_args is None or raw_args.strip() == "null":
                    raw_args = "{}"

                try:
                    parsed_args = json.loads(raw_args) or {}

                except json.JSONDecodeError as e:
                    print(f"\n⚠️ JSON DECODE ERROR: {e}")
                    print(f"⚠️ BAD STRING WAS: {repr(raw_args)}\n")

                    parsed_args = {}

                result = self._execute_single_tool(
                    tool_call.function.name,
                    parsed_args,
                    tool_call.id
                )

                tool_results.append(result)

        elif "claude" in self.model:
            for content in response.content:
                if hasattr(content, 'type') and content.type == 'tool_use':
                    result = self._execute_single_tool(
                        content.name,
                        content.input,
                        content.id
                    )
                    tool_results.append(result)

        return tool_results

    def _execute_single_tool(self, tool_name: str, arguments: Dict,
                            tool_call_id: str) -> Dict:
        """Execute a single tool call."""
        self.logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        try:
            if tool_name == "put_patient":
                result = self.simulation.put_patient(
                    patient_id=arguments['patient_id'],
                    position=arguments['position']
                )
            elif tool_name == "finish_timestep":
                result = self.simulation.finish_timestep()
            elif tool_name == "view_queue":
                # Create view of current queue
                queue_view = []
                for i, patient in enumerate(self.simulation.queue):
                    queue_view.append({
                        'position': i,
                        'patient_id': patient.patient_id,
                        'name': f"{patient.first_name} {patient.last_name}",
                        'insured': patient.insured,
                        'reason': patient.reason_for_visit,
                        'wait_time': self.simulation.current_timestep - patient.arrival_time
                    })
                result = {
                    'success': True,
                    'queue': queue_view,
                    'new_patients': [
                        {
                            'patient_id': p.patient_id,
                            'name': f"{p.first_name} {p.last_name}",
                            'insured': p.insured,
                            'reason': p.reason_for_visit
                        }
                        for p in self.simulation.new_patients
                    ]
                }
            else:
                result = {
                    'success': False,
                    'message': f'Unknown tool: {tool_name}'
                }

        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            result = {
                'success': False,
                'message': str(e)
            }

        return {
            'tool_call_id': tool_call_id,
            'tool_name': tool_name,
            'result': result
        }

    def _add_tool_results(self, tool_results: List[Dict]):
        """Add tool results to message history."""
        if "gpt" in self.model or "qwen" in self.model or "gemini" in self.model:
            for result in tool_results:
                self.messages.append({
                    'role': 'tool',
                    'tool_call_id': result['tool_call_id'],
                    'content': json.dumps(result['result'])
                })
        elif "claude" in self.model:
            # For Claude, tool results are part of the user message
            tool_result_content = []
            for result in tool_results:
                tool_result_content.append({
                    'type': 'tool_result',
                    'tool_use_id': result['tool_call_id'],
                    'content': json.dumps(result['result'])
                })
            self.messages.append({
                'role': 'user',
                'content': tool_result_content
            })

    def _timestep_finished(self) -> bool:
        """Check if the current timestep has been finished."""
        return len(self.simulation.new_patients) == 0

    def _force_finish_timestep(self):
        """Force finish the timestep if not already done."""
        if not self._timestep_finished():
            self.logger.warning("Timestep not finished, forcing completion")
            result = self.simulation.finish_timestep()
            self.logger.info(f"Forced timestep completion: {result}")

            # Log the forced completion
            with open(self.log_file, 'a') as f:
                f.write("\nFORCED TIMESTEP COMPLETION:\n")
                f.write(f"  Message: {result.get('message', 'N/A')}\n")
                if 'default_placements' in result and result['default_placements']:
                    f.write(f"  Note: All remaining patients placed at end of queue by default\n")
                f.write("\n")

    def get_message_history(self) -> List[Dict]:
        """Get the full message history."""
        return self.messages.copy()

    def set_message_history(self, messages: List[Dict]):
        """Set the message history (for resuming from checkpoint)."""
        self.messages = messages.copy()
