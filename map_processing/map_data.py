import math

from matplotlib.pyplot import grid
import numpy as np
import pyvista as pv
import xarray as xr
from map_processing.map_data_provider import BmiOpenTopoMapDataProvider, MapDataProvider
import matplotlib.pyplot as plt


class MapData:
    """Implementation of MapData using xarray."""

    def __init__(self, roi: tuple[int, int, int, int]):
        """Initialize MapData with a region of interest (ROI).
        
        Args:
            roi: A tuple representing the region of interest (north, east, south, west).
        """
        self.roi=roi
        self.map_provider = BmiOpenTopoMapDataProvider()
        self.map_data = None
        self.map_data_corrected = False
        self.mesh = None
        self.mesh_corrected = False
        self.avg_lat = (roi[0] + roi[2]) / 2
        self.x_correction_factor = math.cos(math.radians(self.avg_lat))
        self.resolution_longtitude_x = 92 * self.x_correction_factor  # Default resolution in meters x
        self.resolution_latitude_y = 92  # Default resolution in meters y

    def load_data(self) -> None:
        """Load map data from a provider."""
        self.map_data = self.map_provider.get_map_data(roi=self.roi)

    def create_mesh(self) -> None:
        """Create a mesh from the map data."""
        if self.map_data is None:
            self.load_data()

        elevation_grid = self.map_data.squeeze().values
        x = np.arange(elevation_grid.shape[1])*self.resolution_longtitude_x
        y = np.arange(elevation_grid.shape[0]-1,-1,-1)*self.resolution_latitude_y
        x_2d, y_2d = np.meshgrid(x, y)
        grid = pv.StructuredGrid(x_2d, y_2d, elevation_grid)
        self.mesh = grid.extract_surface(algorithm='dataset_surface').triangulate()

    def scale_mesh(self, factor=2) -> None:
        """Scale the mesh vertically by a given factor for better visualization."""
        if self.mesh is None:
            self.create_mesh()
        self.mesh.scale([1, 1, factor], inplace=True)

    def render(self, screenshot_output_path: str | None = None) -> pv.pyvista_ndarray:
        """Create a mesh from the map data."""
        if self.mesh is None:
            self.create_mesh()
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(self.mesh, color="lightblue", show_edges=True)        
        if screenshot_output_path is not None:
            image = plotter.screenshot(screenshot_output_path)
        else:
            image = plotter.screenshot()
        plotter.close()
        return image
    
    def render_map_data(self, screenshot_output_path: str | None = None) -> pv.pyvista_ndarray:
        """Render the map data as a 2D image."""
        if self.map_data is None:
            self.load_data()
        da = self.map_data.squeeze()
        fig, ax = plt.subplots(figsize=(8, 6))
        da.plot(ax=ax)
        ax.set_title("Map Data")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        plt.tight_layout()
        if screenshot_output_path is not None:
            plt.savefig(screenshot_output_path)
        plt.close(fig)
    
    def save_stl(self, path: str) -> None:
        """Save the mesh as an STL file."""
        if self.mesh is None:
            self.create_mesh()
        self.mesh.save(path)
