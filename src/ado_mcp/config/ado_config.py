"""
Configuration module for Azure DevOps MCP Server.
Handles loading and validating configuration from environment variables.
"""
import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class AzureDevOpsConfig:
    """Configuration for Azure DevOps connection."""
    pat: str  # Changed from personal_access_token to pat
    organization_url: str
    project_name: str

    @property
    def org_url(self) -> str:
        """Alias for organization_url to maintain compatibility."""
        return self.organization_url

    @classmethod
    def load_from_env(cls) -> 'AzureDevOpsConfig':
        """
        Load configuration from environment variables or .env file.
        Supports both ADO_ and AZURE_DEVOPS_ prefixed variables.
        
        Returns:
            AzureDevOpsConfig instance
            
        Raises:
            ValueError: If required configuration is missing
        """
        load_dotenv()
        
        # Try both naming conventions
        pat = (os.getenv('AZURE_DEVOPS_PAT') or 
               os.getenv('ADO_PERSONAL_ACCESS_TOKEN'))
        
        org_url = (os.getenv('AZURE_DEVOPS_ORG_URL') or 
                  os.getenv('ADO_ORGANIZATION_URL'))
                  
        project = (os.getenv('AZURE_DEVOPS_PROJECT') or 
                  os.getenv('ADO_PROJECT_NAME'))

        if not all([pat, org_url, project]):
            logger.error("Azure DevOps configuration is missing")
            raise ValueError("Missing Azure DevOps configuration.")

        return cls(
            pat=pat,
            organization_url=org_url,
            project_name=project
        )
