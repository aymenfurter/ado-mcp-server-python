> [!IMPORTANT]  
> Please consider using the official MCP server:  
> https://github.com/microsoft/azure-devops-mcp


# Azure DevOps MCP Server

This is a Model Context Protocol (MCP) server for Azure DevOps that provides work item management capabilities.

## Prerequisites

- Docker
- Azure DevOps Personal Access Token (PAT) with appropriate permissions
- Azure DevOps Organization and Project details

## Quick Start

1. Build the Docker image:
```bash
docker build -t ado-mcp-server .
```

2. Run the server with environment variables:
```bash
docker run -i --rm \
  -e ADO_PERSONAL_ACCESS_TOKEN="your_pat_here" \
  -e ADO_ORGANIZATION_URL="https://dev.azure.com/your_org" \
  -e ADO_PROJECT_NAME="your_project" \
  ado-mcp-server
```

## Configuration

The server requires the following environment variables:

- `ADO_PERSONAL_ACCESS_TOKEN`: Your Azure DevOps Personal Access Token
- `ADO_ORGANIZATION_URL`: Your Azure DevOps organization URL
- `ADO_PROJECT_NAME`: Your Azure DevOps project name

## VS Code Integration

Add this configuration to your VS Code settings to integrate with the MCP server:

```json
{
    "inputs": [
      {
        "type": "promptString",
        "id": "ado_pat",
        "description": "Azure DevOps Personal Access Token",
        "password": true
      },
      {
        "type": "promptString",
        "id": "ado_org",
        "description": "Azure DevOps Organization URL"
      },
      {
        "type": "promptString",
        "id": "ado_project",
        "description": "Azure DevOps Project Name"
      }
    ],
    "servers": {
      "azuredevops": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "ADO_PERSONAL_ACCESS_TOKEN",
          "-e",
          "ADO_ORGANIZATION_URL",
          "-e",
          "ADO_PROJECT_NAME",
          "ado-mcp-server"
        ],
        "env": {
          "ADO_PERSONAL_ACCESS_TOKEN": "${input:ado_pat}",
          "ADO_ORGANIZATION_URL": "${input:ado_org}",
          "ADO_PROJECT_NAME": "${input:ado_project}"
        }
      }
    }
}
```

## Features

- Search work items
- Create new work items
- Update existing work items
- Get work item states
- Simple command-line interface for testing

## Development

To build and run locally for development:

1. Clone the repository
2. Build the Docker image: `docker build -t ado-mcp-server .`
3. Run the server with your environment variables

## Testing

Run the tests using:
```bash
docker run -i --rm \
  -e ADO_PERSONAL_ACCESS_TOKEN="your_pat_here" \
  -e ADO_ORGANIZATION_URL="https://dev.azure.com/your_org" \
  -e ADO_PROJECT_NAME="your_project" \
  ado-mcp-server python -m pytest
```
