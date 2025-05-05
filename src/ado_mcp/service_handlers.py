"""Service handlers for Azure DevOps services."""
import logging
from typing import Optional, Dict, Any

from .config.ado_config import AzureDevOpsConfig
from .services.work_item_service import WorkItemService
from .services.work_item_states_service import WorkItemStatesService

logger = logging.getLogger(__name__)

class WorkItemServiceHandler:
    """Handler for WorkItemService."""
    
    def __init__(self) -> None:
        """Initialize empty handler."""
        self.service: Optional[WorkItemService] = None
    
    def initialize(self, config: AzureDevOpsConfig) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Azure DevOps configuration object
        """
        try:
            self.service = WorkItemService(config)
            logger.info("WorkItemService initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize WorkItemService")
            raise


class WorkItemStatesServiceHandler:
    """Handler for WorkItemStatesService."""
    
    def __init__(self) -> None:
        """Initialize empty handler."""
        self.service: Optional[WorkItemStatesService] = None
        self.states_cache: Optional[Dict[str, Dict[str, Any]]] = None
    
    def initialize(self, config: AzureDevOpsConfig) -> None:
        """
        Initialize the service with configuration.
        
        Args:
            config: Azure DevOps configuration object
        """
        try:
            self.service = WorkItemStatesService(config)
            logger.info("WorkItemStatesService initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize WorkItemStatesService")
            raise
    
    async def preload_states(self) -> None:
        """
        Preload work item states into cache.
        
        This will improve performance for state-related operations.
        """
        if not self.service:
            logger.error("Cannot preload states - service not initialized")
            return
            
        logger.info("Preloading work item states...")
        try:
            self.states_cache = await self.service.get_all_work_item_states()
            logger.info(f"Successfully loaded states for {len(self.states_cache)} work item types")
        except Exception as e:
            logger.error(f"Failed to preload work item states: {e}")
