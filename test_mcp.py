#!/usr/bin/env python3
"""
Simple test script for MCP servers
"""

import subprocess
import sys
import os
from pathlib import Path

def test_server_imports():
    """Test if the MCP servers can be imported"""
    project_root = Path(__file__).parent
    
    print("Testing MCP server imports...")
    
    # Test subsidy server
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); from servers.subsidy_mcp import SubsidyMCPServer; print('Subsidy server: OK')"
        ], check=True, cwd=project_root, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Subsidy server import failed: {e.stderr}")
    
    # Test price server
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); from servers.price_mcp import PriceMCPServer; print('Price server: OK')"
        ], check=True, cwd=project_root, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Price server import failed: {e.stderr}")
    
    # Test MCP bridge
    try:
        subprocess.run([
            sys.executable, "-c", 
            "import sys; sys.path.insert(0, '.'); from tools.mcp_bridge import MCPBridge; print('MCP Bridge: OK')"
        ], check=True, cwd=project_root, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"MCP Bridge import failed: {e.stderr}")

if __name__ == "__main__":
    test_server_imports()
