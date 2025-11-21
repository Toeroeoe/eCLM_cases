import yaml

import pandas as pd
import numpy as np

from icoscp_core.icos import bootstrap
from icoscp.dobj import Dobj
from icoscp import cpauth




if __name__ == "__main__":
    config = yaml.safe_load(open("config_ICOS.yaml"))

    if not isinstance(config, dict): 
        raise ValueError("Configuration file is empty or not found.")

    cookie_token = config["auth"]["token"]
    
    meta, data = bootstrap.fromCookieToken(cookie_token)
    
    cpauth.init_by(data.auth)
    
    station_id = config["station"]["id"]
    
    datasets = config["datasets"]
    
    station_list = [s.uri for s in meta.list_stations() if s.id == station_id]
    
    datasets_found = []
    
    for m in meta.list_datatypes():
        for d in datasets:
            if d in str(m.label):
                datasets_found.append(m.uri)
                
    station_meta = [m.uri 
                    for m in meta.list_data_objects(station=station_list)
                    if m.datatype_uri in datasets_found]
    
    print("Number of datasets:", len(station_meta))
    
    dfs = [Dobj(station_meta[d]) for d in range(len(station_meta))]
    
    for df in dfs:
        
        print(df.data)
    
    
    
    #meta, data = bootstrap.fromCookieToken(cookie_token)