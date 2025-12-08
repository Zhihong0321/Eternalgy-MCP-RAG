import asyncio
import os
import logging
import traceback

from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from mcp.types import Tool 
from mcp import StdioServerParameters 

logger = logging.getLogger(__name__)

class MCPManager:
    def __init__(self):
        self.server_configs = {} # Stores StdioServerParameters objects

    async def spawn_mcp(self, mcp_id: str, command: str, args: list[str], cwd: str = "/app") -> dict:
        """
        Registers an MCP server configuration. The actual process is spawned per call.
        """
        logger.info(f"Registering MCP {mcp_id} config: command={command}, args={args}, cwd={cwd}")
        server_params = StdioServerParameters(
            command=command,
            args=args,
            cwd=cwd
        )
        self.server_configs[mcp_id] = server_params
        
        logger.info(f"MCP config {mcp_id} registered successfully.")
        return {"mcp_id": mcp_id, "status": "registered"}

    async def terminate_mcp(self, mcp_id: str):
        """
        Removes an MCP server configuration.
        """
        if mcp_id in self.server_configs:
            logger.info(f"Removing MCP config {mcp_id}.")
            del self.server_configs[mcp_id]
        else:
            logger.warning(f"Attempted to terminate non-existent MCP config: {mcp_id}")

    async def get_mcp_status(self, mcp_id: str) -> str:
        """
        Gets the status of an MCP server.
        """
        if mcp_id in self.server_configs:
            return "registered (inactive)"
        return "not found"

    async def list_mcp_tools(self, mcp_id: str) -> list[Tool]:
        """
        Requests the list of tools from an MCP server using its registered config.
        """
        server_params = self.server_configs.get(mcp_id)
        if not server_params:
            raise ValueError(f"MCP config for {mcp_id} not found. Register it first.")
        
        logger.info(f"Spawning temporary process to list tools for MCP {mcp_id}")
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools_data = await session.list_tools()
                    return tools_data.tools 
        except Exception as e:
            logger.error(f"Error listing tools for MCP {mcp_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

    async def call_mcp_tool(self, mcp_id: str, tool_name: str, tool_args: dict) -> dict:
        """
        Calls a specific tool on an MCP server using its registered config.
        """
        server_params = self.server_configs.get(mcp_id)
        if not server_params:
            raise ValueError(f"MCP config for {mcp_id} not found. Register it first.")
        
        logger.info(f"Spawning temporary process to call tool '{tool_name}' on MCP {mcp_id} with args: {tool_args}")
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    return result
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on MCP {mcp_id}: {e}")
            logger.error(traceback.format_exc())
            raise e

    async def shutdown_all_mcps(self):
        """Removes all MCP server configurations."""
        mcp_ids = list(self.server_configs.keys())
        for mcp_id in mcp_ids:
            await self.terminate_mcp(mcp_id)
        self.server_configs.clear()