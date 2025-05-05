"""Work item states management for Azure DevOps."""
import logging
from typing import Dict, List, Any, Optional

from .base_service import AzureDevOpsBaseService

logger = logging.getLogger(__name__)

class WorkItemStatesService(AzureDevOpsBaseService):
    """
    Service for managing work item states in Azure DevOps.
    
    Provides functionality to retrieve valid states and transitions for work items.
    """
    
    async def get_work_item_types(self) -> List[str]:
        """
        Get all work item types available in the project.
        
        Returns:
            List of work item type names
            
        Raises:
            RuntimeError: If retrieval fails
        """
        self.logger.info(f"Getting work item types for project '{self.config.project_name}'")
        try:
            work_item_types = self.wit_client.get_work_item_types(self.config.project_name)
            return [wit.name for wit in work_item_types]
        except Exception as e:
            self.logger.error(f"Failed to get work item types: {e}")
            raise RuntimeError(f"Failed to get work item types: {e}")

    async def get_valid_states(self, work_item_type: str) -> Dict[str, List[str]]:
        """
        Get valid states and state transitions for a work item type.
        
        Args:
            work_item_type: Type of work item to get states for
            
        Returns:
            Dictionary with states as keys and lists of valid reasons as values
            
        Raises:
            RuntimeError: If retrieval fails
        """
        self.logger.info(f"Getting valid states for work item type '{work_item_type}' in project '{self.config.project_name}'")
        try:
            # Get the work item type definition
            wit_type = self.wit_client.get_work_item_type(
                self.config.project_name, work_item_type
            )
            
            # Get the states and handle different API versions/structures
            states_with_reasons = {}
            
            for state in wit_type.states:
                # Different versions of the Azure DevOps API might return different structures
                # Some might have a 'reasons' attribute, some might not
                state_name = getattr(state, 'name', str(state))
                
                # Try different approaches to get reasons based on what the API returns
                reasons = []
                try:
                    # Try to get reasons if available directly
                    if hasattr(state, 'reasons') and state.reasons:
                        reasons = [reason.name for reason in state.reasons]
                    # If no reasons attribute or it's empty, provide a default
                    if not reasons:
                        self.logger.debug(f"No reasons found for state '{state_name}', using default")
                        reasons = [f"Changed to {state_name}"]
                except AttributeError:
                    # If there's an attribute error, use a default reason
                    self.logger.debug(f"Error accessing reasons for state '{state_name}', using default")
                    reasons = [f"Changed to {state_name}"]
                
                states_with_reasons[state_name] = reasons
            
            return states_with_reasons
            
        except Exception as e:
            self.logger.error(f"Failed to get valid states for {work_item_type}: {e}")
            raise RuntimeError(f"Failed to get valid states for {work_item_type}: {e}")

    async def get_all_work_item_states(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Get all work item types and their valid states.
        
        Returns:
            Dictionary with work item types as keys and their states/reasons as values
            
        Raises:
            RuntimeError: If retrieval fails
        """
        self.logger.info(f"Getting all work item types and states for project '{self.config.project_name}'")
        result = {}
        
        try:
            work_item_types = await self.get_work_item_types()
            for wit_type in work_item_types:
                result[wit_type] = await self.get_valid_states(wit_type)
            return result
        except Exception as e:
            self.logger.error(f"Failed to get all work item states: {e}")
            raise RuntimeError(f"Failed to get all work item states: {e}")
