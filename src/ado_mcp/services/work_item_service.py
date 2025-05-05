"""Work item CRUD operations for Azure DevOps."""
import logging
from typing import Dict, List, Any, Optional

from azure.devops.v7_1.work_item_tracking.models import Wiql, WorkItem

from .base_service import AzureDevOpsBaseService

logger = logging.getLogger(__name__)

class WorkItemService(AzureDevOpsBaseService):
    """
    Service for work item CRUD operations in Azure DevOps.
    
    Provides functionality to search, create, and update work items.
    """
    
    async def search_items(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search work items by keywords in title.
        If keyword is empty, returns all work items.
        
        Args:
            keyword: Search keyword for work item titles
            
        Returns:
            List of matching work items with their details
        """
        self.logger.info(f"Searching work items with keyword: '{keyword}' in project '{self.config.project_name}'")
        
        # Base query without title filter
        base_query = f"""
            SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType]
            FROM WorkItems
            WHERE [System.TeamProject] = '{self.config.project_name}'
              AND [System.WorkItemType] <> ''"""
              
        # Add title filter only if keyword is not empty
        if keyword.strip():
            # Escape single quotes in the keyword for WIQL
            escaped_keyword = keyword.replace("'", "''")
            base_query += f"\n              AND [System.Title] CONTAINS '{escaped_keyword}'"
            
        base_query += "\n            ORDER BY [System.ChangedDate] DESC"
        
        wiql_query = Wiql(query=base_query)
        query_result = self.wit_client.query_by_wiql(wiql=wiql_query).work_items
        work_item_ids = [item.id for item in query_result] if query_result else []

        if not work_item_ids:
            self.logger.info("No work items found matching the query.")
            return []

        self.logger.info(f"Found {len(work_item_ids)} work item references. Fetching details...")
        # Fetch details - consider batching for >200 IDs in high-volume scenarios
        work_items = self.wit_client.get_work_items(
            ids=work_item_ids,
            fields=["System.Id", "System.Title", "System.State", "System.WorkItemType", 
                    "System.Reason", "System.Description"]
        )
        results = [self._format_work_item_result(item) for item in work_items]
        self.logger.info(f"Returning details for {len(results)} work items.")
        return results

    def _format_description(self, description: Optional[str]) -> str:
        """
        Format description text by replacing newlines with HTML breaks.
        
        Args:
            description: The description text to format
            
        Returns:
            Formatted description with HTML breaks
        """
        if not description:
            return ""
        formatted_description = description.replace('\n', '<br>')
        return f"<div>{formatted_description}</div>"

    async def create_item(self, work_item_type: str, title: str, 
                          description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new work item.
        
        Args:
            work_item_type: Type of work item to create (e.g., 'Task', 'Bug')
            title: Title for the work item
            description: Optional description for the work item
            
        Returns:
            Newly created work item details
        """
        self.logger.info(f"Creating new '{work_item_type}' with title: '{title}' in project '{self.config.project_name}'")
        fields_to_set = {
            "System.Title": title,
            "System.Description": self._format_description(description)
        }
        patch_document = self._build_patch_document(fields_to_set)

        created_item = self.wit_client.create_work_item(
            project=self.config.project_name,
            type=work_item_type,
            document=patch_document
        )
        self.logger.info(f"Successfully created work item ID: {created_item.id}")
        return self._format_work_item_result(created_item)

    async def update_item(self, work_item_id: int, title: Optional[str] = None, 
                         description: Optional[str] = None, state: Optional[str] = None, 
                         reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing work item.
        
        Args:
            work_item_id: ID of the work item to update
            title: New title (optional)
            description: New description (optional)
            state: New state (optional)
            reason: Reason for state change (required if state is provided)
            
        Returns:
            Updated work item details
            
        Raises:
            ValueError: If state is provided without reason
        """
        self.logger.info(f"Editing work item ID: {work_item_id} in project '{self.config.project_name}'")
        fields_to_update = {
            "System.Title": title,
            "System.Description": self._format_description(description) if description is not None else None,
            "System.State": state,
            "System.Reason": reason
        }
        # Filter out fields that were not provided (are None)
        fields_to_update = {k: v for k, v in fields_to_update.items() if v is not None}

        if state is not None and reason is None:
            self.logger.error("Reason must be provided when updating state for work item ID: %d", work_item_id)
            raise ValueError("A 'reason' must be provided when updating the 'state'.")

        if not fields_to_update:
            self.logger.warning(f"No fields provided to update for work item {work_item_id}.")
            return {"id": work_item_id, "message": "No update fields provided."}

        patch_document = self._build_patch_document(fields_to_update)
        updated_item = self.wit_client.update_work_item(
            id=work_item_id,
            project=self.config.project_name,  # Ensure project is specified
            document=patch_document
        )
        self.logger.info(f"Successfully updated work item ID: {work_item_id}")
        return self._format_work_item_result(updated_item)
