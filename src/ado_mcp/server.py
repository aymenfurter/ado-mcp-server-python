"""FastMCP server implementation for Azure DevOps."""
import asyncio
import logging

from fastmcp import FastMCP

from .config.ado_config import AzureDevOpsConfig
from .service_handlers import WorkItemServiceHandler, WorkItemStatesServiceHandler
from .tools import ADOMCPTools
from .resources import ADOMCPResources

logger = logging.getLogger(__name__)


class ADOMCPServer:
    """
    FastMCP server for Azure DevOps integration.
    
    Manages initialization, configuration, and server lifecycle.
    """
    
    def __init__(self):
        """Initialize server components."""
        self.mcp = FastMCP(
            name="AzureDevOpsWorkItemServer",
            instructions="Provides tools to search, create, and edit Azure DevOps work items."
        )
        # Create handlers first
        self.work_item_handler = WorkItemServiceHandler()
        self.states_handler = WorkItemStatesServiceHandler()
        
        # Pass handlers to tools and resources
        self.tools = ADOMCPTools(self.work_item_handler, self.states_handler)
        self.resources = ADOMCPResources(self.states_handler)
        
        # Register MCP tools
        self.mcp.tool()(self.tools.search_work_items)
        self.mcp.tool()(self.tools.create_work_item)
        self.mcp.tool()(self.tools.edit_work_item)
        self.mcp.tool()(self.tools.get_valid_work_item_states)
    
    def initialize(self, config: AzureDevOpsConfig) -> bool:
        """
        Initialize server with configuration.
        
        Args:
            config: Azure DevOps configuration
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize service handlers
            self.work_item_handler.initialize(config)
            self.states_handler.initialize(config)
            
            # Register the resource for work item states
            self.mcp.add_resource_fn(
                self.resources.get_work_item_states_resource,
                uri="resource://ado-work-item-states",
                name="Azure DevOps Work Item States",
                description="Valid states and reasons for each work item type in the configured Azure DevOps project",
                mime_type="application/json"
            )
            
            # Pre-load states cache
            self._preload_states()
            
            return True
        except Exception as e:
            logger.critical(f"Failed to initialize server: {e}")
            return False
    
    def _preload_states(self) -> None:
        """Preload work item states in a non-blocking way."""
        async def _load():
            await self.states_handler.preload_states()
        
        # Use asyncio to run the coroutine in the current thread
        try:
            asyncio.run(_load())
        except Exception as e:
            logger.error(f"Failed to preload states: {e}")
    
    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting FastMCP server '{self.mcp.name}'...")
        try:
            self.mcp.run() 
        except Exception as e:
            logger.critical(f"FastMCP server '{self.mcp.name}' encountered a fatal error: {e}", exc_info=True)
        finally:
            logger.info(f"FastMCP server '{self.mcp.name}' stopped.")
