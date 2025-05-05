"""
Azure DevOps Work Item MCP Server entry point.

This script initializes and runs the FastMCP server for Azure DevOps integration.
"""
import logging
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.ado_mcp.config import AzureDevOpsConfig
    from src.ado_mcp.server import ADOMCPServer
except ImportError as e:
    traceback.print_exc()
    sys.exit(1)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)
logger = logging.getLogger(__name__)

def main() -> int:
    """
    Main entry point for the MCP server.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Starting Azure DevOps MCP Server...")
    logger.info("Initializing Azure DevOps MCP Server")
    
    try:
        ado_config = AzureDevOpsConfig.load_from_env()
    except ValueError as e:
        error_msg = f"Failed to load Azure DevOps configuration: {e}. Server cannot start."
        logger.critical(error_msg)
        return 1
    except Exception as e:
        error_msg = f"Unexpected error loading configuration: {e}"
        traceback.print_exc()
        logger.critical(error_msg, exc_info=True)
        return 1
    
    try:
        server = ADOMCPServer()
        if not server.initialize(ado_config):
            error_msg = "Failed to initialize server. Exiting."
            print(f"ERROR: {error_msg}")
            logger.critical(error_msg)
            return 1
        
        logger.info(f"Server initialized successfully for project: '{ado_config.project_name}'")
        server.run()
        return 0
    except Exception as e:
        error_msg = f"Unexpected error during server initialization/run: {e}"
        traceback.print_exc()
        logger.critical(error_msg, exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
