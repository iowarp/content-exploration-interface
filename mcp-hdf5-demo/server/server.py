import h5py
from mcp.server.fastmcp import FastMCP
import os

# Path to your HDF5 file (for demo, create a small one if not present)
HDF5_PATH = "demo_data.h5"

def create_demo_hdf5(path):
    if not os.path.exists(path):
        with h5py.File(path, "w") as f:
            grp = f.create_group("group1")
            grp.create_dataset("dataset1", data=[1, 2, 3, 4])
            f.create_dataset("root_dataset", data=[10, 20, 30])

create_demo_hdf5(HDF5_PATH)

mcp = FastMCP("HDF5 Demo Server")

@mcp.resource("hdf5://{path}")
def get_hdf5_resource(path: str) -> str:
    """Fetch a dataset or group from the HDF5 file as a string."""
    with h5py.File(HDF5_PATH, "r") as f:
        if path in f:
            obj = f[path]
            if isinstance(obj, h5py.Dataset):
                return str(obj[()])
            elif isinstance(obj, h5py.Group):
                return f"Group contains: {list(obj.keys())}"
            else:
                return "Unknown object type."
        else:
            return f"Path '{path}' not found."

@mcp.tool()
def list_hdf5_paths() -> str:
    """List all datasets and groups in the HDF5 file."""
    paths = []
    def visitor(name, obj):
        paths.append(name)
    with h5py.File(HDF5_PATH, "r") as f:
        f.visititems(visitor)
    return "\n".join(paths)

if __name__ == "__main__":
    mcp.run()
