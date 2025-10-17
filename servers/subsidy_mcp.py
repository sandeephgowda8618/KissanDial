#!/usr/bin/env python3
"""
Subsidy MCP Server for KissanDial
Provides subsidies information through Model Context Protocol
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

import pandas as pd
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import BaseModel

# Add the project root to Python path to import from other modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SubsidyQuery(BaseModel):
    query: str
    max_results: int = 5

class SubsidyMCPServer:
    def __init__(self):
        self.server = Server("subsidy-server")
        self.df = None
        self.load_subsidies_data()
        self.setup_handlers()

    def load_subsidies_data(self):
        """Load subsidies data from CSV file"""
        try:
            csv_path = project_root / "data" / "subsidies" / "central" / "main_subsidy_data.csv"
            if csv_path.exists():
                self.df = pd.read_csv(csv_path)
                print(f"Loaded {len(self.df)} subsidy records", file=sys.stderr)
            else:
                print(f"Warning: CSV file not found at {csv_path}", file=sys.stderr)
                self.df = pd.DataFrame()  # Empty dataframe as fallback
        except Exception as e:
            print(f"Error loading subsidies data: {e}", file=sys.stderr)
            self.df = pd.DataFrame()

    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="subsidy_search",
                    description="Search for government subsidies for farmers. Query can include crop types, equipment, location, or other farming needs.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for subsidies (e.g., 'tractor', 'seeds', 'Karnataka', 'crop insurance')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_subsidy_categories",
                    description="Get available categories of subsidies",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_subsidy_by_state",
                    description="Get subsidies filtered by state",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "State name (e.g., 'Karnataka', 'Tamil Nadu')"
                            }
                        },
                        "required": ["state"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
            """Handle tool calls"""
            if arguments is None:
                arguments = {}
                
            try:
                if name == "subsidy_search":
                    return await self.search_subsidies(arguments)
                elif name == "get_subsidy_categories":
                    return await self.get_categories()
                elif name == "get_subsidy_by_state":
                    return await self.get_subsidies_by_state(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )]

    async def search_subsidies(self, arguments: dict) -> list[TextContent]:
        """Search for subsidies based on query"""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        
        if self.df.empty:
            return [TextContent(
                type="text",
                text="No subsidy data available. Please check if the CSV file is loaded correctly."
            )]

        # Simple text search across all columns
        search_results = []
        query_lower = query.lower()
        
        for _, row in self.df.iterrows():
            # Search in all text columns
            row_text = " ".join([str(val).lower() for val in row.values if pd.notna(val)])
            if query_lower in row_text:
                search_results.append(row)
                
        # Limit results
        search_results = search_results[:max_results]
        
        if not search_results:
            return [TextContent(
                type="text",
                text=f"No subsidies found for query: '{query}'. Try different keywords like 'tractor', 'seeds', 'insurance', or state names."
            )]

        # Format results
        result_text = f"Found {len(search_results)} subsidies for '{query}':\n\n"
        
        for i, row in enumerate(search_results, 1):
            result_text += f"{i}. "
            # Format subsidy information
            for col in self.df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    result_text += f"{col}: {row[col]}\n   "
            result_text += "\n"
            
        return [TextContent(type="text", text=result_text)]

    async def get_categories(self) -> list[TextContent]:
        """Get available subsidy categories"""
        if self.df.empty:
            return [TextContent(
                type="text",
                text="No subsidy data available."
            )]
            
        # Extract unique categories if there's a category column
        categories = []
        for col in self.df.columns:
            if 'category' in col.lower() or 'type' in col.lower():
                unique_values = self.df[col].dropna().unique()
                categories.extend(unique_values)
        
        if not categories:
            categories = ["General subsidies available"]
            
        result_text = "Available subsidy categories:\n\n"
        for i, category in enumerate(sorted(set(categories)), 1):
            result_text += f"{i}. {category}\n"
            
        return [TextContent(type="text", text=result_text)]

    async def get_subsidies_by_state(self, arguments: dict) -> list[TextContent]:
        """Get subsidies filtered by state"""
        state = arguments.get("state", "")
        
        if self.df.empty:
            return [TextContent(
                type="text",
                text="No subsidy data available."
            )]
            
        # Search for state in all columns
        state_lower = state.lower()
        state_results = []
        
        for _, row in self.df.iterrows():
            row_text = " ".join([str(val).lower() for val in row.values if pd.notna(val)])
            if state_lower in row_text:
                state_results.append(row)
                
        if not state_results:
            return [TextContent(
                type="text",
                text=f"No subsidies found for state: '{state}'. Available states may vary in the dataset."
            )]
            
        result_text = f"Subsidies available in {state}:\n\n"
        
        for i, row in enumerate(state_results[:10], 1):  # Limit to 10 results
            result_text += f"{i}. "
            for col in self.df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    result_text += f"{col}: {row[col]}\n   "
            result_text += "\n"
            
        return [TextContent(type="text", text=result_text)]

async def main():
    """Main function to run the MCP server"""
    server_instance = SubsidyMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
