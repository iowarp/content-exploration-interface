import asyncio
from mcp import ClientSession
from mcp.client.local import local_client

async def main():
    # Connect to the local MCP server (default port 8080)
    async with local_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("Available tools:")
            tools = await session.list_tools()
            for tool in tools:
                print("-", tool)

            print("\nAvailable resources:")
            resources = await session.list_resources()
            for resource in resources:
                print("-", resource)

            # List all HDF5 paths using the tool
            result = await session.call_tool("list_hdf5_paths")
            print("\nHDF5 paths in server:")
            print(result)

            # Fetch a specific dataset as a resource
            dataset_path = "group1/dataset1"
            resource_uri = f"hdf5://{dataset_path}"
            content, mime_type = await session.read_resource(resource_uri)
            print(f"\nFetched resource '{resource_uri}':")
            print(content)

if __name__ == "__main__":
    asyncio.run(main())
