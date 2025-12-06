"""
MCP Client Module - Mock Implementation
Demonstrates MCP integration concept without actual MCP SDK dependencies
"""
import os
import logging
import time
import requests
from typing import Dict, List, Any
from datetime import datetime


class MCPClient:
    """Mock MCP Client for demonstration purposes"""

    def __init__(self):
        self.available_tools: Dict[str, List[Dict]] = {}
        self.is_connected = False
        self.logger = logging.getLogger(__name__)

        # Mock tools for demonstration
        self.mock_tools = {
            "brave_search": [
                {
                    "name": "search",
                    "description": "Search the web using Brave Search",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ],
            "web": [
                {
                    "name": "fetch",
                    "description": "Fetch and extract text content from a webpage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL of the webpage to fetch"
                            }
                        },
                        "required": ["url"]
                    }
                }
            ],
            "filesystem": [
                {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to read"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write content to a file (creates or overwrites)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "list_files",
                    "description": "List files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path"
                            }
                        }
                    }
                }
            ]
        }

    def initialize_servers(self) -> List[str]:
        """Initialize mock MCP servers"""
        try:
            self.logger.info("Initializing mock MCP servers...")

            # Simulate connection delay
            time.sleep(0.5)

            connected_servers = []
            brave_api_key = os.getenv('BRAVE_API_KEY')

            # Add Brave Search if API key available
            if brave_api_key:
                self.available_tools["brave_search"] = self.mock_tools["brave_search"]
                connected_servers.append("brave_search")
                self.logger.info("✅ Brave Search mock server initialized")
            else:
                self.logger.warning("⚠️  Brave API key not found, skipping Brave Search")

            # Always add web fetch
            self.available_tools["web"] = self.mock_tools["web"]
            connected_servers.append("web")
            self.logger.info("✅ Web fetch server initialized")

            # Always add filesystem
            self.available_tools["filesystem"] = self.mock_tools["filesystem"]
            connected_servers.append("filesystem")
            self.logger.info("✅ Filesystem mock server initialized")

            self.is_connected = True
            self.logger.info(f"✅ MCP initialization complete: {len(connected_servers)} servers")

            return connected_servers

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize mock servers: {str(e)}")
            return []

    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a mock MCP tool with improved error handling"""
        try:
            self.logger.info(f"🔧 Calling tool: {server_name}.{tool_name} with args {arguments}")

            # Simulate API delay
            time.sleep(0.3)

            # Mock implementations
            if server_name == "brave_search" and tool_name == "search":
                return self._mock_brave_search(arguments)

            elif server_name == "web" and tool_name == "fetch":
                return self._web_fetch(arguments)

            elif server_name == "filesystem" and tool_name == "read_file":
                return self._mock_read_file(arguments)

            elif server_name == "filesystem" and tool_name == "write_file":
                return self._mock_write_file(arguments)

            elif server_name == "filesystem" and tool_name == "list_files":
                return self._mock_list_files(arguments)

            error_msg = f"Tool '{tool_name}' not found on server '{server_name}'"
            self.logger.warning(f"⚠️  {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_type": "ToolNotFound"
            }

        except KeyError as e:
            error_msg = f"Missing required parameter: {str(e)}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "InvalidParameters"
            }
        except ValueError as e:
            error_msg = f"Invalid parameter value: {str(e)}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "ValidationError"
            }
        except Exception as e:
            error_msg = f"Unexpected error calling tool {tool_name}: {str(e)}"
            self.logger.error(f"❌ {error_msg}", exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "error_type": "InternalError"
            }

    def _mock_brave_search(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Real Brave Search API implementation"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)

        brave_api_key = os.getenv('BRAVE_API_KEY')

        if not brave_api_key:
            return {
                "success": False,
                "error": "BRAVE_API_KEY not found in environment variables"
            }

        try:
            # Brave Search API endpoint
            url = "https://api.search.brave.com/res/v1/web/search"

            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": brave_api_key
            }

            params = {
                "q": query,
                "count": min(max_results, 20)  # Brave API allows max 20 results
            }

            self.logger.info(f"🔍 Calling Brave Search API for: {query}")
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code != 200:
                error_msg = f"Brave API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {response.text[:200]}"

                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

            data = response.json()

            # Format search results
            results_text = f"🔍 Brave Search Results for: '{query}'\n\n"

            web_results = data.get("web", {}).get("results", [])

            if not web_results:
                results_text += "No results found.\n"
            else:
                for idx, result in enumerate(web_results[:max_results], 1):
                    title = result.get("title", "No title")
                    url = result.get("url", "")
                    description = result.get("description", "No description available")

                    # Get extra snippets for more detailed information
                    extra_snippets = result.get("extra_snippets", [])

                    results_text += f"{idx}. **{title}**\n"
                    results_text += f"   URL: {url}\n"
                    results_text += f"   Description: {description}\n"

                    # Add extra snippets if available (often contain specific data like prices)
                    if extra_snippets:
                        results_text += f"   Additional info:\n"
                        for snippet in extra_snippets[:3]:  # Limit to 3 snippets
                            results_text += f"   - {snippet}\n"

                    results_text += "\n"

            # Add query info if available
            query_info = data.get("query", {})
            if query_info:
                original_query = query_info.get("original", query)
                results_text += f"📊 Query: {original_query}\n"
                results_text += f"🔢 Results shown: {len(web_results[:max_results])} of {len(web_results)} total\n"

            self.logger.info(f"✅ Brave Search returned {len(web_results)} results")

            return {
                "success": True,
                "result": {
                    "type": "text",
                    "content": results_text
                }
            }

        except requests.exceptions.Timeout:
            error_msg = "Brave Search API request timed out"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Brave Search API request failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error in Brave Search: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def _mock_read_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Real file read implementation with security restrictions"""
        path = arguments.get("path", "")

        try:
            # Expand user home directory (~)
            path = os.path.expanduser(path)

            # Convert to absolute path
            abs_path = os.path.abspath(path)

            # Security check: don't allow reading sensitive system files
            forbidden_patterns = [
                '/etc/passwd', '/etc/shadow', '/etc/sudoers',
                '/.ssh/', '/private/etc/', '/.aws/', '/.env'
            ]

            for pattern in forbidden_patterns:
                if pattern in abs_path.lower():
                    return {
                        "success": False,
                        "error": f"Access denied: Cannot read sensitive file {path}"
                    }

            # Check if file exists
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "error": f"File not found: {path}"
                }

            # Check if it's a file (not a directory)
            if not os.path.isfile(abs_path):
                return {
                    "success": False,
                    "error": f"Path is not a file: {path}"
                }

            # Get file info
            file_size = os.path.getsize(abs_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(abs_path)).strftime('%Y-%m-%d %H:%M:%S')

            # Check file size (max 1MB for safety)
            if file_size > 1024 * 1024:
                return {
                    "success": False,
                    "error": f"File too large: {file_size} bytes (max 1MB)"
                }

            # Read file content
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try binary read for non-text files
                with open(abs_path, 'rb') as f:
                    content = f"[Binary file - cannot display as text]\nSize: {file_size} bytes"

            result_text = f"📄 File: {abs_path}\n\n"
            result_text += f"{'=' * 70}\n"
            result_text += f"Size: {file_size:,} bytes\n"
            result_text += f"Last Modified: {mod_time}\n"
            result_text += f"{'=' * 70}\n\n"
            result_text += content

            self.logger.info(f"✅ Successfully read file: {abs_path} ({file_size:,} bytes)")

            return {
                "success": True,
                "result": {
                    "type": "text",
                    "content": result_text
                }
            }

        except PermissionError:
            error_msg = f"Permission denied: Cannot read {path}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Error reading file: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def _mock_write_file(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file with security restrictions"""
        path = arguments.get("path", "")
        content = arguments.get("content", "")

        try:
            # Expand user home directory (~)
            path = os.path.expanduser(path)

            # Convert to absolute path
            abs_path = os.path.abspath(path)

            # Security check: don't allow writing to sensitive locations
            forbidden_patterns = [
                '/etc/', '/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/',
                '/private/etc/', '/System/', '/Library/', '/.ssh/', '/.aws/'
            ]

            for pattern in forbidden_patterns:
                if pattern in abs_path:
                    return {
                        "success": False,
                        "error": f"Access denied: Cannot write to system location {path}"
                    }

            # Ensure parent directory exists
            parent_dir = os.path.dirname(abs_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    self.logger.info(f"📁 Created directory: {parent_dir}")
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Cannot create directory {parent_dir}: {str(e)}"
                    }

            # Check if file already exists
            file_existed = os.path.exists(abs_path)

            # Write file content
            try:
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error writing file: {str(e)}"
                }

            # Get file info
            file_size = os.path.getsize(abs_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(abs_path)).strftime('%Y-%m-%d %H:%M:%S')

            action = "Updated" if file_existed else "Created"
            result_text = f"💾 {action} File: {abs_path}\n\n"
            result_text += f"{'=' * 70}\n"
            result_text += f"Size: {file_size:,} bytes\n"
            result_text += f"Written: {mod_time}\n"
            result_text += f"{'=' * 70}\n\n"
            result_text += f"✅ Successfully wrote {len(content)} characters to file"

            self.logger.info(f"✅ Successfully wrote file: {abs_path} ({file_size:,} bytes)")

            return {
                "success": True,
                "result": {
                    "type": "text",
                    "content": result_text
                }
            }

        except PermissionError:
            error_msg = f"Permission denied: Cannot write to {path}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Error writing file: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def _mock_list_files(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Real directory listing implementation with security restrictions"""
        path = arguments.get("path", ".")

        try:
            # Expand user home directory (~)
            path = os.path.expanduser(path)

            # Convert to absolute path
            abs_path = os.path.abspath(path)

            # Check if directory exists
            if not os.path.exists(abs_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {path}"
                }

            # Check if it's a directory
            if not os.path.isdir(abs_path):
                return {
                    "success": False,
                    "error": f"Path is not a directory: {path}"
                }

            # List directory contents
            try:
                entries = os.listdir(abs_path)
            except PermissionError:
                return {
                    "success": False,
                    "error": f"Permission denied: Cannot list directory {path}"
                }

            # Sort entries: directories first, then files
            entries.sort(key=lambda x: (not os.path.isdir(os.path.join(abs_path, x)), x.lower()))

            result_text = f"📁 Directory: {abs_path}\n\n"
            result_text += f"{'=' * 70}\n"

            file_count = 0
            dir_count = 0

            for entry in entries:
                entry_path = os.path.join(abs_path, entry)

                try:
                    stat_info = os.stat(entry_path)
                    size = stat_info.st_size
                    mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime('%b %d %H:%M')

                    if os.path.isdir(entry_path):
                        result_text += f"📂 {entry}/\n"
                        result_text += f"   Modified: {mod_time}\n\n"
                        dir_count += 1
                    else:
                        result_text += f"📄 {entry}\n"
                        result_text += f"   Size: {size:,} bytes | Modified: {mod_time}\n\n"
                        file_count += 1

                except (OSError, PermissionError):
                    result_text += f"❌ {entry} (cannot access)\n\n"

            result_text += f"{'=' * 70}\n"
            result_text += f"Total: {len(entries)} items ({file_count} files, {dir_count} directories)\n"

            self.logger.info(f"✅ Successfully listed directory: {abs_path} ({len(entries)} items)")

            return {
                "success": True,
                "result": {
                    "type": "text",
                    "content": result_text
                }
            }

        except Exception as e:
            error_msg = f"Error listing directory: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def _web_fetch(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and extract text content from a webpage"""
        url = arguments.get("url", "")

        if not url:
            return {
                "success": False,
                "error": "URL parameter is required"
            }

        try:
            from bs4 import BeautifulSoup

            self.logger.info(f"🌐 Fetching webpage: {url}")

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Limit to first 3000 chars to avoid huge responses
            if len(text) > 3000:
                text = text[:3000] + "\n\n[Content truncated - showing first 3000 characters]"

            result_text = f"🌐 Webpage: {url}\n\n{text}"

            self.logger.info(f"✅ Successfully fetched webpage ({len(text)} chars)")

            return {
                "success": True,
                "result": {
                    "type": "text",
                    "content": result_text
                }
            }

        except requests.exceptions.Timeout:
            error_msg = "Request timed out - webpage took too long to respond"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e.response.status_code}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except ImportError:
            error_msg = "BeautifulSoup4 library not installed. Run: pip install beautifulsoup4"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Error fetching webpage: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    def get_available_tools(self) -> Dict[str, List[Dict]]:
        """Get all available mock tools"""
        return self.available_tools

    def get_status(self) -> Dict[str, Any]:
        """Get connection status"""
        tools_count = sum(len(tools) for tools in self.available_tools.values())

        return {
            "connected": self.is_connected,
            "servers": list(self.available_tools.keys()),
            "tools_count": tools_count
        }


# Global MCP client instance
mcp_client = MCPClient()
