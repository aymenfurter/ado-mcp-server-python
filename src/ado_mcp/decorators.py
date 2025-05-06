"""Decorators for MCP tools."""
import functools
import logging
from typing import Any, Callable, TypeVar, cast

from fastmcp import Context

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def handle_ado_errors(func: F) -> F:
    """
    Decorator for handling errors in MCP tools.
    
    Provides consistent error handling for Azure DevOps service calls.
    
    Args:
        func: MCP tool function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: Context, *args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__
        try:
            await ctx.info(f"Executing tool: {tool_name}")
            result = await func(self, ctx, *args, **kwargs)
            await ctx.info(f"Tool {tool_name} executed successfully.")
            return result
        except ValueError as ve:
            logger.error(f"Validation error in {tool_name}: {ve}")
            await ctx.error(f"Input validation error for {tool_name}: {ve}")
            return {"error": "Validation Error", "message": str(ve)}
        except ConnectionError as ce:
            logger.error(f"Connection error during {tool_name}: {ce}")
            await ctx.error(f"Azure DevOps connection error during {tool_name}: {ce}")
            return {"error": "Connection Error", "message": "Failed to connect to Azure DevOps."}
        except RuntimeError as re:
            # Specifically for service operation failures like update failures
            logger.error(f"Service error in {tool_name}: {re}")
            await ctx.error(f"Azure DevOps service error in {tool_name}: {re}")
            return {"error": "Service Error", "message": str(re), "details": getattr(re, "__cause__", None)}
        except Exception as e:
            # Check if this is an Azure DevOps service error
            error_str = str(e)
            if "AzureDevOpsServiceError" in error_str or "azure.devops.exceptions" in error_str:
                error_message = error_str
                if "Reason" in error_str and "not in the list of supported values" in error_str:
                    # Special handling for the reason field error
                    await ctx.error(f"The provided reason is not valid for this state transition.")
                    return {"error": "Invalid Reason", "message": "The reason provided is not supported for this state change."}
                
                # Generic Azure DevOps service error
                logger.error(f"Azure DevOps service error in {tool_name}: {error_message}")
                await ctx.error(f"Azure DevOps service error: {error_message}")
                return {"error": "Azure DevOps Error", "message": error_message}
            
            # Other unexpected errors
            logger.exception(f"Unexpected error in {tool_name}: {e}")
            await ctx.error(f"An unexpected error occurred in {tool_name}: {e}")
            return {"error": "Server Error", "message": "An internal server error occurred."}
    
    return cast(F, wrapper)

def validate_service(func: F) -> F:
    """
    Decorator for validating service availability in MCP tools.
    
    Ensures the service is initialized before executing the tool.
    
    Args:
        func: MCP tool function to wrap
        
    Returns:
        Wrapped function with service validation
    """
    @functools.wraps(func)
    async def wrapper(self, ctx: Context, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(self, 'work_item_handler') and not hasattr(self, 'states_handler'):
            logger.critical("Class does not have required service handlers")
            raise RuntimeError("Service handlers not initialized.")

        if (hasattr(self, 'work_item_handler') and self.work_item_handler.service is None) or \
           (hasattr(self, 'states_handler') and self.states_handler.service is None):
            logger.critical("Service not initialized before tool execution.")
            raise RuntimeError("Service not initialized.")

        return await func(self, ctx, *args, **kwargs)
    
    return cast(F, wrapper)
