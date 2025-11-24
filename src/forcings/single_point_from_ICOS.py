from functools import reduce
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
    
    dataset_found_names = []
    
    for m in meta.list_datatypes():
        for d in datasets:
            if d in str(m.label):
                datasets_found.append(m.uri)
                dataset_found_names.append(m.label)
                
    print("General number of datasets found: ", len(datasets_found))
    print("Dataset URIs found: ", datasets_found)
    print("Datasets found: ", dataset_found_names)
    
#    station_meta = []
#    station_meta_names = []
#    
#    for m in meta.list_data_objects(station=station_list):
#        
#        if m.datatype_uri in datasets_found:
#
#            station_meta.append(m.uri)
#            station_meta_names.extend([n.label 
#                                       for n in meta.list_datatypes() 
#                                       if n.uri == m.datatype_uri])
    
#    print("Number of datasets at station: ", len(station_meta))
#    print("Dataset URIs at station: ", station_meta)
#    print("Dataset names at station: ", station_meta_names)
    
    station_doj_uris = [meta.list_data_objects(station=station_list,
                                                datatype=d)[0].uri
                        for d in datasets_found]
    
    dfs = []
    
    for i, s in enumerate(station_doj_uris):
        
        print("Loading data object: ", dataset_found_names[i])
        dobj = Dobj(s)
        df = dobj.data
        print("Data loaded with shape: ", df.shape)
        dfs.append(df)

    df_all = pd.DataFrame()

    for i in range(len(dfs)):
        
        if i == 0:
            
            df_all = pd.concat([df_all, dfs[i]], ignore_index=True)
            
        else:
    
            df_all = pd.merge(df_all, 
                              dfs[i],
                              how="outer", 
                              on="TIMESTAMP",
                              suffixes=(None, '_' + dataset_found_names[i]))
            
    df_all = df_all.set_index("TIMESTAMP").sort_index()
    
    df_all.to_csv(f"ICOS_single_point_{station_id}.csv")
            
    
    
    
        
        
    
    
    
    #meta, data = bootstrap.fromCookieToken(cookie_token)