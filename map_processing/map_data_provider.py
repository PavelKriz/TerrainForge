from abc import ABC, abstractmethod
from typing import Any, Dict, List
import xarray
from bmi_topography import Topography


class MapDataProvider(ABC):
    """Abstract base class for map data providers."""

    @abstractmethod
    def get_map_data(self, roi: tuple[int, int, int, int]):
        """
        Retrieve map data for a given region of interest (ROI).
        
        Args:
            roi: A tuple representing the region of interest (north, east, south, west).
            
        Returns:
            Map data in a format suitable for further processing (e.g., xarray.DataArray).
        """
        pass


class BmiOpenTopoMapDataProvider(MapDataProvider):
    """Implementation that reads map data using the bmi_topography library from open-topography."""

    def __init__(self, api_key_path: str):
        self.geo_params = Topography.DEFAULT.copy()
        api_key_file = open(api_key_path, "r")
        self.api_key = api_key_file.read().strip()
        api_key_file.close()
        self.geo_params["api_key"] = self.api_key

    def get_map_data(self, roi: tuple[int, int, int, int]) -> xarray.DataArray:
        """Load map data from file for the given location."""
        # Implementation here
        export_params = self.geo_params.copy()
        export_params["north"] = roi[0]
        export_params["east"] = roi[1]
        export_params["south"] = roi[2]
        export_params["west"] = roi[3]
        topo = Topography(**export_params)
        topo.fetch()
        topo.load()
        return topo.da