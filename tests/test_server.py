"""Unit tests for Azure DevOps MCP Server components."""
import pytest
import os
from unittest.mock import patch, MagicMock

# Import necessary components from refactored structure
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ado_mcp.config.ado_config import AzureDevOpsConfig
from src.ado_mcp.services.work_item_service import WorkItemService
from src.ado_mcp.services.work_item_states_service import WorkItemStatesService


@pytest.fixture
def mock_ado_connection():
    """Mocks the azure.devops.connection.Connection and its client."""
    with patch('src.ado_mcp.services.base_service.Connection', autospec=True) as mock_conn_class:
        mock_connection = MagicMock()
        mock_wit_client = MagicMock()
        mock_connection.clients.get_work_item_tracking_client.return_value = mock_wit_client
        mock_conn_class.return_value = mock_connection
        yield mock_conn_class, mock_wit_client


@patch('src.ado_mcp.config.ado_config.load_dotenv')
def test_config_load_success(mock_load_dotenv, monkeypatch):
    """Tests successful loading of config from environment variables."""
    monkeypatch.setenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/testorg")
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "testpat")
    monkeypatch.setenv("AZURE_DEVOPS_PROJECT", "testproject")

    config = AzureDevOpsConfig.load_from_env()
    assert config.org_url == "https://dev.azure.com/testorg"
    assert config.pat == "testpat"
    assert config.project_name == "testproject"
    mock_load_dotenv.assert_called_once()

@patch('src.ado_mcp.config.ado_config.load_dotenv')
def test_config_load_missing_variable(mock_load_dotenv, monkeypatch):
    """Tests config loading failure when a variable is missing."""
    monkeypatch.setenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/testorg")
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "testpat")
    monkeypatch.delenv("AZURE_DEVOPS_PROJECT", raising=False)

    with pytest.raises(ValueError, match="Missing Azure DevOps configuration."):
        AzureDevOpsConfig.load_from_env()
    mock_load_dotenv.assert_called_once()


def test_service_init_success(mock_ado_connection):
    """Tests successful initialization of AzureDevOpsBaseService."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    try:
        service = WorkItemService(config=mock_config)
        assert service.config == mock_config
        assert service.wit_client is not None
        # Check if Connection was called correctly
        mock_conn_class, _ = mock_ado_connection
        mock_conn_class.assert_called_once()
    except ConnectionError:
        pytest.fail("Service initialization failed unexpectedly.")

@patch('src.ado_mcp.services.base_service.Connection', side_effect=Exception("Mock Connection Failure"))
def test_service_init_connection_failure(mock_conn_class):
    """Tests service initialization failure when Connection fails."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    with pytest.raises(ConnectionError, match="Failed to connect to Azure DevOps: Mock Connection Failure"):
        WorkItemService(config=mock_config)


@pytest.mark.asyncio
async def test_search_items_success(mock_ado_connection, mocker):
    """Tests successful work item search."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection

    # Mock the response from query_by_wiql
    mock_query_result = MagicMock()
    mock_query_result.work_items = [MagicMock(id=1), MagicMock(id=2)]
    mock_wit_client.query_by_wiql.return_value = mock_query_result

    # Mock the response from get_work_items
    mock_item1 = MagicMock()
    mock_item1.id = 1
    mock_item1.url = "url1"
    mock_item1.fields = {"System.Title": "Test Item 1", "System.State": "New", "System.WorkItemType": "Task"}
    mock_item2 = MagicMock()
    mock_item2.id = 2
    mock_item2.url = "url2"
    mock_item2.fields = {"System.Title": "Test Item 2", "System.State": "Active", "System.WorkItemType": "Bug"}
    mock_wit_client.get_work_items.return_value = [mock_item1, mock_item2]

    service = WorkItemService(config=mock_config)
    results = await service.search_items(keyword="test")

    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[0]["title"] == "Test Item 1"
    assert results[1]["id"] == 2
    assert results[1]["state"] == "Active"
    mock_wit_client.query_by_wiql.assert_called_once()
    mock_wit_client.get_work_items.assert_called_once()

@pytest.mark.asyncio
async def test_search_items_no_results(mock_ado_connection, mocker):
    """Tests work item search with no results."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection

    # Mock the response from query_by_wiql to return no items
    mock_query_result = MagicMock()
    mock_query_result.work_items = []
    mock_wit_client.query_by_wiql.return_value = mock_query_result

    service = WorkItemService(config=mock_config)
    results = await service.search_items(keyword="nonexistent")
    
    assert isinstance(results, list)
    assert len(results) == 0
    mock_wit_client.query_by_wiql.assert_called_once()
    mock_wit_client.get_work_items.assert_not_called()

# --- Work Item Creation/Update Tests ---

@pytest.mark.asyncio
async def test_create_work_item_success(mock_ado_connection):
    """Tests successful work item creation."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection
    
    # Mock the response from create_work_item
    mock_item = MagicMock()
    mock_item.id = 3
    mock_item.url = "url3"
    mock_item.fields = {
        "System.Title": "New Task",
        "System.State": "New",
        "System.WorkItemType": "Task",
        "System.Description": "Task description"
    }
    mock_wit_client.create_work_item.return_value = mock_item
    
    service = WorkItemService(config=mock_config)
    result = await service.create_item(
        work_item_type="Task",
        title="New Task",
        description="Task description"
    )
    
    assert result["id"] == 3
    assert result["title"] == "New Task"
    assert result["state"] == "New"
    assert result["description"] == "Task description"
    mock_wit_client.create_work_item.assert_called_once()

@pytest.mark.asyncio
async def test_update_work_item_success(mock_ado_connection):
    """Tests successful work item update."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection
    
    # Mock the response from update_work_item
    mock_updated_item = MagicMock()
    mock_updated_item.id = 4
    mock_updated_item.url = "url4"
    mock_updated_item.fields = {
        "System.Title": "Updated Task",
        "System.State": "Active",
        "System.WorkItemType": "Task",
        "System.Reason": "Work started",
        "System.Description": "Updated description"
    }
    mock_wit_client.update_work_item.return_value = mock_updated_item
    
    service = WorkItemService(config=mock_config)
    result = await service.update_item(
        work_item_id=4,
        title="Updated Task",
        description="Updated description",
        state="Active",
        reason="Work started"
    )
    
    assert result["id"] == 4
    assert result["title"] == "Updated Task"
    assert result["state"] == "Active"
    assert result["reason"] == "Work started"
    assert result["description"] == "Updated description"
    mock_wit_client.update_work_item.assert_called_once()

@pytest.mark.asyncio
async def test_update_work_item_state_without_reason(mock_ado_connection):
    """Tests that updating a work item state without reason raises ValueError."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection
    
    service = WorkItemService(config=mock_config)
    
    with pytest.raises(ValueError, match="A 'reason' must be provided when updating the 'state'."):
        await service.update_item(
            work_item_id=5,
            state="Active",  # Providing state without reason
        )
    
    # Assert that update_work_item was not called
    mock_wit_client.update_work_item.assert_not_called()

# --- Work Item States Tests ---

@pytest.mark.asyncio
async def test_get_work_item_types(mock_ado_connection):
    """Tests getting work item types."""
    mock_config = AzureDevOpsConfig(
        organization_url="url",
        pat="pat", 
        project_name="proj"
    )
    _, mock_wit_client = mock_ado_connection
    
    # Mock the response from get_work_item_types
    mock_type1 = MagicMock()
    mock_type1.name = "Task"
    mock_type2 = MagicMock()
    mock_type2.name = "Bug"
    mock_wit_client.get_work_item_types.return_value = [mock_type1, mock_type2]
    
    service = WorkItemStatesService(config=mock_config)
    result = await service.get_work_item_types()
    
    assert isinstance(result, list)
    assert len(result) == 2
    assert "Task" in result
    assert "Bug" in result
    mock_wit_client.get_work_item_types.assert_called_once_with("proj")

