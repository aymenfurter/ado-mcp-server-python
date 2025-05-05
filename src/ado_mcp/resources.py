"""MCP resources for Azure DevOps."""
import logging
from typing import Dict, Any

from fastmcp import Context

from .service_handlers import WorkItemStatesServiceHandler

logger = logging.getLogger(__name__)

class ADOMCPResources:
    """Handles MCP resources for Azure DevOps."""
    
    def __init__(self, states_handler: WorkItemStatesServiceHandler):
        """
        Initialize with a states handler.
        
        Args:
            states_handler: Handler for work item states service
        """
        self.states_handler = states_handler
    
    async def get_work_item_states_resource(self, context: Context) -> Dict[str, Any]:
        """
        Resource function to return work item states.
        
        Args:
            context: MCP Context
            
        Returns:
            Dictionary with work item states information
        """
        # Return from cache if available
        if self.states_handler.states_cache:
            return self.states_handler.states_cache
        
        # Otherwise try to load on demand
        if self.states_handler.service:
            try:
                states = await self.states_handler.service.get_all_work_item_states()
                # Update cache for future requests
                self.states_handler.states_cache = states
                return states
            except Exception as e:
                logger.error(f"Failed to load work item states for resource: {e}")
                return {"error": f"Failed to load work item states: {str(e)}"}
        
        return {"error": "Work item states service not initialized"}
