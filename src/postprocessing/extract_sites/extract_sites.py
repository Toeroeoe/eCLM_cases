import glob
import yaml
import os
import numpy as np
import pandas as pd
#import xarray as xr
import netCDF4 as nc


def grid_to_points(lat: np.ndarray, 
                   lon: np.ndarray) -> np.ndarray:
    """
    Create an array of lat/lon pairs from 2D lat and lon arrays.

    Args:
        lat (np.ndarray): latitudes
        lon (np.ndarray): longitudes

    Returns:
        np.ndarray: Array of shape (n_points, 2) with lat/lon pairs.
    """
    return np.dstack([lat, lon]).reshape(-1, 2)


def closest_cell(coords_point: np.ndarray, 
                 coords_cells: np.ndarray, 
                 shape: tuple[int]) -> tuple[tuple, np.ndarray]:
    
    """
    Find the closest coordinate point.
    Given a point in 2d coordinates,
    and a list of points find the node.
    
    Args:
        coords_point (np.ndarray): point coordinates (2,) [lat, lon]
        coords_cells (np.ndarray): array of cell coordinates (n_cells, 2) [lat, lon]
        shape (tuple[int]): shape of the original grid
        
    Returns:
        tuple[tuple, np.ndarray]: index of the closest cell in the grid,
                                  coordinates of the closest cell
    """
   
    deltas          = np.subtract(coords_cells, coords_point)
    dist            = np.einsum('ij,ij->i', deltas, deltas)
    
    closest_i       = np.nanargmin(dist)
    closest_coords  = coords_cells[closest_i, :]
    closest_cell    = np.unravel_index(closest_i, shape)
    return closest_cell, closest_coords


if __name__ == "__main__":
    
    config = yaml.safe_load(open("config_extract_sites.yaml"))
    
    if not isinstance(config, dict): raise ValueError("Config file is empty or invalid.")
    
    file_stations = glob.glob(config["stations"]["path"])    
    if len(file_stations) != 1:
        raise FileNotFoundError(f"No or multiple station file(s) found at {config['stations']['path']}")

    ds_stations = pd.read_csv(file_stations[0])
    
    lats = ds_stations[config["stations"]["lat_col"]].to_numpy()
    lons = ds_stations[config["stations"]["lon_col"]].to_numpy()
    ids = ds_stations[config["stations"]["id_col"]].to_numpy()
    
    assert len(lats) == len(lons), "Latitude and Longitude columns must have the same length."

    file_data = glob.glob(config["data"]["path"])
    if len(file_data) == 0:
        raise FileNotFoundError(f"No data files found at {config['data']['path']}")
    elif len(file_data) == 1:
        ds_data = nc.Dataset(file_data[0])
    else:
        ds_data = nc.MFDataset(sorted(file_data), aggdim="time")

    time = nc.num2date(ds_data.variables["time"][:],
                     units=ds_data.variables["time"].units, 
                     calendar=ds_data.variables["time"].calendar)
    
    var = ds_data.variables[config["data"]["var_name"]][:]
    
    file_geo = glob.glob(config["geo"]["path"])
    if len(file_geo) == 0:
        raise FileNotFoundError(f"No geo files found at {config['geo']['path']}")
    else:
        ds_geo = nc.Dataset(file_geo[0])
    
    lat2d = ds_geo[config["geo"]["lat_name"]][:]
    lon2d = ds_geo[config["geo"]["lon_name"]][:]

    cells = grid_to_points(lat2d, lon2d)
    
    cols = []
    
    for i, (lat, lon) in enumerate(zip(lats, lons)):
        
        [lat_i, lon_i], closest_coords = closest_cell(np.array([lat, lon]), cells, lat2d.shape)
        
        if var.ndim == 4:
            raise NotImplementedError("4D variables not implemented yet.")
            
        elif var.ndim == 3:
            array_i = var[..., lat_i, lon_i]
            
        else:
            raise NotImplementedError(f"Variable with ndim = {var.ndim} not implemented.")
        
        cols.append(pd.DataFrame(array_i, 
                                 index=np.array(time), 
                                 columns=[f"site_{ids[i]}_{config['data']['var_name']} [{config['data']['var_unit']}]"]))
        
    df_out = pd.concat(cols, axis=1, copy=False)

    os.makedirs(os.path.dirname(config["out"]["path"]), exist_ok=True)
    df_out.to_csv(config["out"]["path"], index_label="time")