"""MCP tools for Azure DevOps operations."""
import logging
from typing import Dict, List, Any, Optional

from fastmcp import Context

from .decorators import handle_ado_errors, validate_service
from .service_handlers import WorkItemServiceHandler, WorkItemStatesServiceHandler

logger = logging.getLogger(__name__)


class ADOMCPTools:
    """Azure DevOps MCP tools."""
    
    def __init__(self, work_item_handler: WorkItemServiceHandler, states_handler: WorkItemStatesServiceHandler) -> None:
        """
        Initialize tool handlers.
        
        Args:
            work_item_handler: The work item service handler
            states_handler: The work item states service handler
        """
        self.work_item_handler = work_item_handler
        self.states_handler = states_handler
    
    @handle_ado_errors
    @validate_service
    async def search_work_items(self, ctx: Context, *, keyword: str) -> List[Dict[str, Any]]:
        """
        Searches Azure DevOps work items by title keyword.
        If keyword is empty, returns all work items.
        
        Args:
            ctx: MCP Context
            keyword: Search term for work item titles. Empty string returns all items.
            
        Returns:
            List of work items (ID, Title, State, Type, URL)
        """
        handler = self.work_item_handler
        return await handler.service.search_items(keyword.strip())

    @handle_ado_errors
    @validate_service
    async def create_work_item(self, ctx: Context, *, work_item_type: str, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new Azure DevOps work item.
        
        Args:
            ctx: MCP Context
            work_item_type: Type like 'Bug', 'Task', 'User Story'
            title: The title for the new work item
            description: Optional description
            
        Returns:
            Details of the created work item (ID, Title, State, Type, URL)
            
        Raises:
            ValueError: If work_item_type or title is missing
        """
        handler = self.work_item_handler
        
        if not work_item_type or not title:
            raise ValueError("work_item_type and title are required.")
            
        return await handler.service.create_item(work_item_type, title, description)

    @handle_ado_errors
    @validate_service
    async def edit_work_item(self, ctx: Context, *, work_item_id: int, title: Optional[str] = None, 
                           description: Optional[str] = None, state: Optional[str] = None, 
                           reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Edits an existing Azure DevOps work item. Provide only the fields to update.
        
        Args:
            ctx: MCP Context
            work_item_id: The ID of the work item to edit
            title: New title (optional)
            description: New description (optional)
            state: New state (e.g., 'Active', 'Resolved') (optional)
            reason: Reason for state change (required if state is updated)
            
        Returns:
            Details of the updated work item or an error message
            
        Raises:
            ValueError: If work_item_id is invalid
        """
        handler = self.work_item_handler
            
        if work_item_id <= 0:
             raise ValueError("work_item_id must be a positive integer.")
             
        return await handler.service.update_item(work_item_id, title, description, state, reason)

    @handle_ado_errors
    @validate_service
    async def get_valid_work_item_states(self, ctx: Context, *, work_item_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves valid states for a specific work item type or all work item types.
        
        Args:
            ctx: MCP Context
            work_item_type: Optional. If provided, returns states only for this type.
                          Otherwise returns states for all work item types.
        
        Returns:
            Dictionary containing valid states and their associated reasons.
            
        Examples:
            For a specific work item type:
            ```json
            {
                "New": ["New"],
                "Active": ["Started work"],
                "Done": ["Completed"]
            }
            ```
            
            For all work item types:
            ```json
            {
                "Task": {
                    "New": ["New"],
                    "Active": ["Started work"],
                    "Done": ["Completed"]
                },
                "Bug": {
                    "New": ["New"],
                    "Active": ["Approved"],
                    "Resolved": ["Fixed"]
                }
            }
            ```
        """
        handler = self.states_handler
        
        # If we have a cached version and it's a request for all states, use cache
        if work_item_type is None and handler.states_cache is not None:
            return handler.states_cache
            
        if work_item_type:
            return await handler.service.get_valid_states(work_item_type)
        else:
            result = await handler.service.get_all_work_item_states()
            # Update cache for future requests
            handler.states_cache = result
            return result
