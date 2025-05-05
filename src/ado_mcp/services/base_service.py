"""Base services for Azure DevOps interactions."""
import logging
from abc import ABC
from typing import Dict, List, Any, Optional

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import WorkItem
from msrest.authentication import BasicAuthentication

from ..config.ado_config import AzureDevOpsConfig

logger = logging.getLogger(__name__)

class AzureDevOpsBaseService(ABC):
    """
    Base class for Azure DevOps services.
    
    Provides common functionality and client initialization.
    """
    
    def __init__(self, config: AzureDevOpsConfig):
        """
        Initialize the service with configuration.
        
        Args:
            config: Azure DevOps configuration object
            
        Raises:
            ConnectionError: If connection to Azure DevOps fails
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        try:
            credentials = BasicAuthentication('', self.config.pat)
            connection = Connection(base_url=self.config.org_url, creds=credentials)
            self.wit_client = connection.clients.get_work_item_tracking_client()
            self.logger.info("Successfully connected to Azure DevOps.")
        except Exception as e:
            self.logger.exception("Failed to connect to Azure DevOps.")
            raise ConnectionError(f"Failed to connect to Azure DevOps: {e}") from e
    
    def _build_patch_document(self, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Builds a JSON Patch document from a dictionary of fields.
        
        Args:
            fields: Dictionary of field names to values
            
        Returns:
            List of patch operations to apply
        """
        patch_document = []
        for field, value in fields.items():
            if value is not None:  # Only include fields that are explicitly set
                # Use System.* field names directly if provided, otherwise assume custom/other field
                field_path = f"/fields/{field}" if field.startswith("System.") else f"/fields/{field}"
                patch_document.append({"op": "add", "path": field_path, "value": value})
        return patch_document
    
    def _format_work_item_result(self, work_item: Any) -> Dict[str, Any]:
        """
        Formats a WorkItem object into a dictionary for API responses.
        
        Args:
            work_item: Azure DevOps WorkItem object
            
        Returns:
            Formatted dictionary with work item details
        """
        # Safely access fields through the fields property
        fields = {}
        if hasattr(work_item, 'fields') and work_item.fields:
            if isinstance(work_item.fields, dict):
                fields = work_item.fields
            else:
                # Handle case where fields might be an object with attributes
                fields = {
                    "System.Title": getattr(work_item.fields, "System.Title", None),
                    "System.State": getattr(work_item.fields, "System.State", None),
                    "System.WorkItemType": getattr(work_item.fields, "System.WorkItemType", None),
                    "System.Reason": getattr(work_item.fields, "System.Reason", None),
                    "System.Description": getattr(work_item.fields, "System.Description", None)
                }
        
        result = {
            "id": getattr(work_item, 'id', None),
            "title": fields.get("System.Title"),
            "state": fields.get("System.State"),
            "type": fields.get("System.WorkItemType"),
            "reason": fields.get("System.Reason"),
            "description": fields.get("System.Description"),
            "url": getattr(work_item, 'url', None)
        }
        # Filter out None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
