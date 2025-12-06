"""
Pipeline Agent Module for Day 10 AI Application
Implements automated MCP pipeline where tools are combined into a sequence
and executed step by step
"""
import re
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from mcp_client import mcp_client
from config import OPENAI_MODEL


class PipelineAgent:
    """
    Autonomous agent that executes multi-step MCP tool pipelines

    The agent can:
    1. Plan which tools to use based on user query
    2. Execute tools step-by-step
    3. Use results from previous steps as input for next steps
    4. Synthesize final answer from all collected data
    """

    def __init__(self, client: OpenAI, memory_storage=None):
        """
        Initialize Pipeline Agent

        Args:
            client: OpenAI client instance
            memory_storage: Optional memory storage for persistence
        """
        if not client:
            raise ValueError("OpenAI client is required")

        self.client = client
        self.memory = memory_storage
        self.logger = logging.getLogger(__name__)
        self.max_steps = 10  # Maximum pipeline steps to prevent infinite loops

    def execute_pipeline(self, user_query: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Execute autonomous MCP pipeline based on user query

        Args:
            user_query: User's question or task
            temperature: AI temperature setting

        Returns:
            dict: Pipeline execution result with steps and final answer
        """
        self.logger.info(f"🚀 Starting pipeline for query: {user_query}")

        # Pipeline execution context
        context = {
            "query": user_query,
            "steps": [],
            "tools_used": [],
            "errors": []
        }

        # System prompt for pipeline planning
        system_prompt = self._get_pipeline_system_prompt()

        # Initial messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        step_number = 0
        pipeline_complete = False

        try:
            while step_number < self.max_steps and not pipeline_complete:
                step_number += 1
                self.logger.info(f"📍 Pipeline Step {step_number}/{self.max_steps}")

                # Ask AI what to do next
                response = self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=1024
                )

                ai_response = response.choices[0].message.content
                self.logger.info(f"🤖 AI Response (Step {step_number}): {ai_response[:100]}...")

                # Check if AI wants to use MCP tools
                mcp_commands = self._extract_mcp_commands(ai_response)

                if mcp_commands:
                    # Execute MCP tools
                    self.logger.info(f"🔧 Found {len(mcp_commands)} MCP commands to execute")

                    executed_tools = []
                    for cmd in mcp_commands:
                        tool_result = self._execute_mcp_command(cmd)

                        # Record step
                        context["steps"].append({
                            "step": step_number,
                            "command": cmd,
                            "result": tool_result,
                            "success": tool_result.get("success", False)
                        })

                        if not tool_result.get("success"):
                            context["errors"].append({
                                "step": step_number,
                                "command": cmd,
                                "error": tool_result.get("error", "Unknown error")
                            })

                        # Track unique tools used
                        tool_key = f"{cmd['server']}.{cmd['tool']}"
                        if tool_key not in context["tools_used"]:
                            context["tools_used"].append(tool_key)

                        # Collect tool execution info for structured message
                        # Limit result size to prevent memory leak
                        result_content = tool_result.get("result", {}).get("content", "")
                        if len(result_content) > 1000:
                            result_content = result_content[:1000] + "\n...[truncated for brevity]"

                        executed_tools.append({
                            "tool": f"{cmd['server']}.{cmd['tool']}",
                            "arguments": cmd.get("arguments", {}),
                            "success": tool_result.get("success", False),
                            "result": result_content,
                            "error": tool_result.get("error") if not tool_result.get("success") else None
                        })

                    # Build structured tool results message
                    tool_results_msg = "\n=== TOOL EXECUTION RESULTS ===\n"
                    for idx, tool_info in enumerate(executed_tools, 1):
                        tool_results_msg += f"\n{idx}. Tool: {tool_info['tool']}\n"
                        tool_results_msg += f"   Arguments: {tool_info['arguments']}\n"
                        if tool_info['success']:
                            tool_results_msg += f"   ✅ Success\n"
                            tool_results_msg += f"   Result: {tool_info['result']}\n"
                        else:
                            tool_results_msg += f"   ❌ Failed: {tool_info['error']}\n"
                    tool_results_msg += "\n=== END RESULTS ===\n"

                    # Add AI's original response
                    messages.append({"role": "assistant", "content": ai_response})

                    # Add structured tool results as user message
                    messages.append({
                        "role": "user",
                        "content": f"{tool_results_msg}\n\nIMPORTANT: Use the ACTUAL data from the tool results above. Based on these results, continue with the next step or provide the final answer. Use [MCP_DONE] when finished."
                    })

                else:
                    # No MCP commands - check if pipeline is done
                    if "[MCP_DONE]" in ai_response or step_number >= self.max_steps:
                        pipeline_complete = True
                        final_answer = ai_response.replace("[MCP_DONE]", "").strip()

                        self.logger.info(f"✅ Pipeline complete after {step_number} steps")

                        result = {
                            "success": True,
                            "answer": final_answer,
                            "steps": context["steps"],
                            "tools_used": context["tools_used"],
                            "total_steps": step_number,
                            "errors": context["errors"]
                        }

                        # Save to memory if available
                        if self.memory:
                            try:
                                self.memory.save_pipeline_execution(user_query, result)
                            except Exception as e:
                                self.logger.error(f"Failed to save pipeline to memory: {e}")

                        return result
                    else:
                        # AI didn't use tools and didn't signal done - ask to continue
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({
                            "role": "user",
                            "content": "Please continue with the next step or use [MCP_DONE] if finished."
                        })

            # Max steps reached
            self.logger.warning(f"⚠️ Pipeline reached max steps ({self.max_steps})")

            return {
                "success": False,
                "error": f"Pipeline exceeded maximum steps ({self.max_steps})",
                "answer": "Pipeline did not complete within step limit",
                "steps": context["steps"],
                "tools_used": context["tools_used"],
                "total_steps": step_number,
                "errors": context["errors"]
            }

        except Exception as e:
            self.logger.error(f"❌ Pipeline error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "answer": f"Pipeline failed: {str(e)}",
                "steps": context["steps"],
                "tools_used": context["tools_used"],
                "total_steps": step_number,
                "errors": context["errors"]
            }

    def _get_pipeline_system_prompt(self) -> str:
        """Get system prompt for pipeline agent"""
        return """You are an autonomous pipeline agent that uses MCP tools to answer complex queries.

IMPORTANT: Always respond in the SAME LANGUAGE as the user's query.
- If user asks in Ukrainian, respond in Ukrainian
- If user asks in English, respond in English
- If user asks in Russian, respond in Russian

AVAILABLE MCP TOOLS (THESE ARE YOUR ONLY TOOLS):
1. **brave_search.search** - Search the web and GET RESULTS
   Usage: [MCP_SEARCH: query]
   Example: [MCP_SEARCH: Python 3.12 new features]
   NOTE: This returns actual data - you MUST use the results!

2. **web.fetch** - Fetch and read a webpage (NEW!)
   Usage: [MCP_WEB_FETCH: url]
   Example: [MCP_WEB_FETCH: https://coinmarketcap.com]
   NOTE: This extracts text from web pages - use for getting real data!

3. **filesystem.read_file** - Read file contents
   Usage: [MCP_READ_FILE: /path/to/file]
   Example: [MCP_READ_FILE: ~/projects/app.py]

4. **filesystem.write_file** - Write content to file
   Usage: [MCP_WRITE_FILE: /path/to/file | content here]
   Example: [MCP_WRITE_FILE: ~/notes.txt | This is the content]

5. **filesystem.list_files** - List directory contents
   Usage: [MCP_LIST_FILES: /path/to/dir]
   Example: [MCP_LIST_FILES: ~/projects]

IMPORTANT - HOW TO GET REAL DATA:
- ✅ Use [MCP_SEARCH] to find URLs
- ✅ Use [MCP_WEB_FETCH: url] to read webpage content and get REAL prices/data
- ✅ Extract actual data from fetched pages
- ❌ NEVER make up data - always fetch it first!

PIPELINE EXECUTION RULES:
1. Break complex tasks into steps
2. Use ONE tool at a time per response
3. **CRITICAL: YOU MUST USE ACTUAL DATA FROM TOOL RESULTS - NEVER FABRICATE OR GUESS DATA**
4. **CRITICAL: After receiving search results, you MUST extract and use the REAL data from those results**
5. Wait for tool results before deciding next step
6. Base your next action ONLY on actual data received from previous tools
7. When task is complete, respond with final answer and add [MCP_DONE] marker

EXAMPLE PIPELINE:
User: "Research Python 3.12 features and save summary"

Step 1: "I'll search for Python 3.12 information. [MCP_SEARCH: Python 3.12 new features]"
→ (receives search results)

Step 2: "Based on the search results I received, I found these features: [lists ACTUAL features from search results]. I'll save this. [MCP_WRITE_FILE: ~/python_3.12_features.md | # Python 3.12 Features\n\n[ACTUAL data from search results]]"
→ (receives write confirmation)

Step 3: "Task complete! I've researched Python 3.12 features and saved a summary with the actual data to ~/python_3.12_features.md. [MCP_DONE]"

CRITICAL RULES TO PREVENT HALLUCINATION:
- ❌ NEVER make up prices, dates, numbers, or facts
- ❌ NEVER use outdated information from your training data
- ❌ NEVER say "I will visit website" - you cannot browse websites!
- ❌ NEVER repeat the same search more than twice
- ✅ ALWAYS extract real data from tool results that you receive
- ✅ ALWAYS verify you have actual results before writing files
- ✅ After 1-2 searches, you should have enough data - extract it and save to file
- ✅ If search results are unclear, search again with different query (max 2 times)

IMPORTANT:
- Execute tools ONE AT A TIME (not all at once)
- Always use [MCP_DONE] when finished
- Be concise and focused
- Chain tool results into next step
- USE REAL DATA ONLY - NO FABRICATION
"""

    def _extract_mcp_commands(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract MCP commands from AI response

        Args:
            text: AI response text

        Returns:
            list: List of MCP command dictionaries
        """
        commands = []

        # Pattern 1: [MCP_SEARCH: query]
        search_pattern = r'\[MCP_SEARCH:\s*([^\]]+)\]'
        for match in re.finditer(search_pattern, text):
            commands.append({
                "type": "search",
                "server": "brave_search",
                "tool": "search",
                "arguments": {"query": match.group(1).strip(), "max_results": 5},
                "original": match.group(0)
            })

        # Pattern 2: [MCP_WEB_FETCH: url]
        fetch_pattern = r'\[MCP_WEB_FETCH:\s*([^\]]+)\]'
        for match in re.finditer(fetch_pattern, text):
            commands.append({
                "type": "web_fetch",
                "server": "web",
                "tool": "fetch",
                "arguments": {"url": match.group(1).strip()},
                "original": match.group(0)
            })

        # Pattern 3: [MCP_READ_FILE: path]
        read_pattern = r'\[MCP_READ_FILE:\s*([^\]]+)\]'
        for match in re.finditer(read_pattern, text):
            commands.append({
                "type": "read_file",
                "server": "filesystem",
                "tool": "read_file",
                "arguments": {"path": match.group(1).strip()},
                "original": match.group(0)
            })

        # Pattern 3: [MCP_WRITE_FILE: path | content]
        write_pattern = r'\[MCP_WRITE_FILE:\s*([^|]+)\|([^\]]+)\]'
        for match in re.finditer(write_pattern, text):
            commands.append({
                "type": "write_file",
                "server": "filesystem",
                "tool": "write_file",
                "arguments": {
                    "path": match.group(1).strip(),
                    "content": match.group(2).strip()
                },
                "original": match.group(0)
            })

        # Pattern 4: [MCP_LIST_FILES: path]
        list_pattern = r'\[MCP_LIST_FILES:\s*([^\]]+)\]'
        for match in re.finditer(list_pattern, text):
            commands.append({
                "type": "list_files",
                "server": "filesystem",
                "tool": "list_files",
                "arguments": {"path": match.group(1).strip()},
                "original": match.group(0)
            })

        return commands

    def _execute_mcp_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single MCP command

        Args:
            command: Command dictionary with server, tool, arguments

        Returns:
            dict: Tool execution result
        """
        try:
            server = command["server"]
            tool = command["tool"]
            args = command["arguments"]

            self.logger.info(f"🔧 Executing: {server}.{tool}({args})")

            result = mcp_client.call_tool(server, tool, args)

            if result.get("success"):
                self.logger.info(f"✅ Tool executed successfully: {server}.{tool}")
            else:
                self.logger.warning(f"⚠️ Tool failed: {result.get('error', 'Unknown error')}")

            return result

        except Exception as e:
            self.logger.error(f"❌ Error executing command: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _replace_mcp_with_results(self, text: str, steps: List[Dict[str, Any]]) -> str:
        """
        Replace MCP commands in text with their results

        Args:
            text: Original text with MCP commands
            steps: Executed pipeline steps

        Returns:
            str: Text with MCP commands replaced by results
        """
        processed = text

        for step in steps:
            if "command" not in step or "result" not in step:
                continue

            original_cmd = step["command"].get("original", "")
            result = step["result"]

            if not original_cmd:
                continue

            if result.get("success"):
                result_content = result.get("result", {}).get("content", "")
                replacement = f"\n\n{result_content}\n"
            else:
                error_msg = result.get("error", "Unknown error")
                replacement = f"\n\n⚠️ Error: {error_msg}\n"

            processed = processed.replace(original_cmd, replacement)

        return processed


# Global pipeline agent instance (will be initialized by app.py)
pipeline_agent = None


def initialize_pipeline_agent(client: OpenAI, memory_storage=None) -> PipelineAgent:
    """
    Initialize global pipeline agent

    Args:
        client: OpenAI client instance
        memory_storage: Optional memory storage for persistence

    Returns:
        PipelineAgent: Initialized agent
    """
    global pipeline_agent
    pipeline_agent = PipelineAgent(client, memory_storage)
    logging.getLogger(__name__).info("✅ Pipeline Agent initialized")
    return pipeline_agent


def get_pipeline_agent() -> Optional[PipelineAgent]:
    """
    Get global pipeline agent instance

    Returns:
        PipelineAgent or None: Global agent instance
    """
    return pipeline_agent
