"""
MCP File & Directory Management Server
Provides tools for file system operations including directory creation, file creation, listing, and searching.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import glob
import re
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "File & Directory Management Server",
    port=int(os.getenv("PORT", "8001"))
)


@mcp.tool()
def create_directory(dirPath: str) -> Dict[str, Any]:
    """
    Create a new directory structure in the workspace.
    Will recursively create all directories in the path, like mkdir -p.
    
    Args:
        dirPath: The absolute path to the directory to create
        
    Returns:
        Success status and created path
    """
    try:
        path = Path(dirPath)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dirPath}")
        return {
            "success": True,
            "path": str(path.absolute()),
            "message": f"Directory created successfully: {dirPath}"
        }
    except Exception as e:
        logger.error(f"Error creating directory {dirPath}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def create_file(filePath: str, content: str) -> Dict[str, Any]:
    """
    Create a new file in the workspace with specified content.
    The directory will be created if it does not already exist.
    
    Args:
        filePath: The absolute path to the file to create
        content: The content to write to the file
        
    Returns:
        Success status and file information
    """
    try:
        path = Path(filePath)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        path.write_text(content, encoding='utf-8')
        
        logger.info(f"Created file: {filePath}")
        return {
            "success": True,
            "path": str(path.absolute()),
            "size": len(content),
            "message": f"File created successfully: {filePath}"
        }
    except Exception as e:
        logger.error(f"Error creating file {filePath}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def list_dir(path: str) -> Dict[str, Any]:
    """
    List the contents of a directory.
    Result will have the name of the child. If the name ends in /, it's a folder, otherwise a file.
    
    Args:
        path: The absolute path to the directory to list
        
    Returns:
        List of directory contents with type indicators
    """
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory does not exist: {path}"
            }
        
        if not dir_path.is_dir():
            return {
                "success": False,
                "error": f"Path is not a directory: {path}"
            }
        
        contents = []
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                contents.append(f"{item.name}/")
            else:
                contents.append(item.name)
        
        logger.info(f"Listed directory: {path} ({len(contents)} items)")
        return {
            "success": True,
            "path": str(dir_path.absolute()),
            "contents": contents,
            "count": len(contents)
        }
    except Exception as e:
        logger.error(f"Error listing directory {path}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def file_search(query: str, maxResults: Optional[int] = None) -> Dict[str, Any]:
    """
    Search for files in the workspace by glob pattern.
    This only returns the paths of matching files.
    
    Examples:
    - **/*.{js,ts} to match all js/ts files in the workspace
    - src/** to match all files under the top-level src folder
    - **/foo/**/*.js to match all js files under any foo folder
    
    Args:
        query: Glob pattern to match files
        maxResults: Maximum number of results to return (optional)
        
    Returns:
        List of matching file paths
    """
    try:
        # Get workspace root (current directory or specified)
        workspace_root = Path.cwd()
        
        # Perform glob search
        matches = []
        for match in workspace_root.glob(query):
            if match.is_file():
                matches.append(str(match.relative_to(workspace_root)))
                if maxResults and len(matches) >= maxResults:
                    break
        
        logger.info(f"File search for '{query}': found {len(matches)} matches")
        return {
            "success": True,
            "query": query,
            "matches": matches,
            "count": len(matches),
            "truncated": maxResults is not None and len(matches) >= maxResults
        }
    except Exception as e:
        logger.error(f"Error in file search '{query}': {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def grep_search(
    query: str,
    isRegexp: bool,
    includePattern: Optional[str] = None,
    maxResults: Optional[int] = None,
    includeIgnoredFiles: bool = False
) -> Dict[str, Any]:
    """
    Fast text search in the workspace using exact string or regex patterns.
    
    Args:
        query: Pattern to search for (supports regex if isRegexp=True)
        isRegexp: Whether the pattern is a regex
        includePattern: Glob pattern to filter files (optional)
        maxResults: Maximum number of results to return (optional)
        includeIgnoredFiles: Include files normally ignored by .gitignore (optional)
        
    Returns:
        Search results with file paths, line numbers, and matched content
    """
    try:
        workspace_root = Path.cwd()
        
        # Compile regex pattern if needed
        if isRegexp:
            pattern = re.compile(query, re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(query), re.IGNORECASE)
        
        # Determine which files to search
        if includePattern:
            files_to_search = list(workspace_root.glob(includePattern))
        else:
            files_to_search = list(workspace_root.rglob("*"))
        
        # Filter to only files
        files_to_search = [f for f in files_to_search if f.is_file()]
        
        # Filter out ignored files if needed
        if not includeIgnoredFiles:
            # Simple .gitignore check (can be enhanced)
            files_to_search = [
                f for f in files_to_search
                if not any(part.startswith('.') for part in f.parts)
                and 'node_modules' not in f.parts
                and '__pycache__' not in f.parts
            ]
        
        results = []
        for file_path in files_to_search:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if pattern.search(line):
                        results.append({
                            "file": str(file_path.relative_to(workspace_root)),
                            "line": line_num,
                            "content": line.strip(),
                            "match": pattern.search(line).group()
                        })
                        
                        if maxResults and len(results) >= maxResults:
                            break
                
                if maxResults and len(results) >= maxResults:
                    break
                    
            except Exception as e:
                # Skip files that can't be read
                continue
        
        logger.info(f"Grep search for '{query}': found {len(results)} matches")
        return {
            "success": True,
            "query": query,
            "isRegexp": isRegexp,
            "results": results,
            "count": len(results),
            "truncated": maxResults is not None and len(results) >= maxResults
        }
    except Exception as e:
        logger.error(f"Error in grep search '{query}': {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.resource("doc://file-directory-api")
def get_api_docs() -> str:
    """API documentation for File & Directory Management Server"""
    return """
    # File & Directory Management Server API
    
    ## Tools
    
    1. create_directory(dirPath: str)
       - Create directory structure recursively
       
    2. create_file(filePath: str, content: str)
       - Create new file with content
       
    3. list_dir(path: str)
       - List directory contents
       
    4. file_search(query: str, maxResults: int)
       - Search files by glob pattern
       
    5. grep_search(query: str, isRegexp: bool, ...)
       - Search file contents by text/regex
    """


async def main():
    """Start the MCP server"""
    logger.info("🚀 Starting File & Directory Management MCP Server...")
    logger.info(f"📂 Workspace root: {Path.cwd()}")
    
    await mcp.run_async(
        transport="sse",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001"))
    )


if __name__ == "__main__":
    asyncio.run(main())
