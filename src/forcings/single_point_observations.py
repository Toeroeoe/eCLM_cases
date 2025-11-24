import os
import datetime
import pytz
import numpy as np
import netCDF4 as nc
import pandas as pd
from pint import UnitRegistry


# Settings
infile: str = 'ICOS_single_point_FI-Hyy.csv'
outdir: str = './out/'

var_names: dict[str, str | None] = {'PRECTmms': 'P', 
                                    'PSRF': 'PA', 
                                    'FSDS': 'SW_IN', 
                                    'FLDS': 'LW_IN', 
                                    'RH': 'RH', 
                                    'TBOT': 'TA', 
                                    'WIND': 'WS'}

src_units: dict[str, str | None] = {'PRECTmms': 'mm/h',
                                    'PSRF': 'kPa',
                                    'FSDS': 'W/m^2',
                                    'FLDS': 'W/m^2',
                                    'RH': '%',
                                    'TBOT': '°C',
                                    'WIND': 'm/s'}


scaling_factors: dict[str, float | None] = {'PRECTmms': 0.5,  # hourly to half-hourly
                                            'PSRF': 1,
                                            'FSDS': 1,
                                            'FLDS': 1,
                                            'RH': 1,
                                            'TBOT': 1,
                                            'WIND': 1}

dst_units: dict[str, str | None] = {'PRECTmms': 'mm/s',
                                    'PSRF': 'Pa',
                                    'FSDS': 'W/m^2',
                                    'FLDS': 'W/m^2',
                                    'RH': '%',
                                    'TBOT': 'K',
                                    'WIND': 'm/s'}

time_col: str = 'TIMESTAMP'
time_format: str = '%Y-%m-%d %H:%M:%S'
start_year: int = 2020
end_year: int = 2020
start_month: int = 1
end_month: int = 1
t_res: str = '1h'

lon: float = 20.00
lat: float = 61.85

latlon_buffer: float = 0.01  

na_values = ["-9999", "-9999.0"]


# Main code, don't change anything below this line unless you know what you're doing
if __name__ == "__main__":
    
    # Class for unit handling
    Q_ = UnitRegistry().Quantity
    
    # Handle negative latitudes
    lonbuffer = latlon_buffer
    latbuffer = latlon_buffer if lat >= 0 else -latlon_buffer

    # reading in data
    data = pd.read_csv(infile, na_values=na_values)

    # Convert 'TIMESTAMP_START' to datetime format and set as index
    data[time_col] = pd.to_datetime(data[time_col], format=time_format)
    data.set_index(time_col, inplace=True)

    site_dates = data.index.to_series().apply(lambda x: x.tz_localize(pytz.utc))
    years = np.arange(start_year, end_year + 1)
    t_per_h = site_dates.resample(t_res).mean().count() / site_dates.resample('1h').mean().count()

    # Collect all the data
    prec_vals  = data[var_names['PRECTmms']].to_numpy()
    prs_vals   = data[var_names['PSRF']].to_numpy()
    fsds_vals  = data[var_names['FSDS']].to_numpy()
    flds_vals  = data[var_names['FLDS']].to_numpy()
    q_vals     = data[var_names['RH']].to_numpy()
    temp_vals  = data[var_names['TBOT']].to_numpy()
    wind_vals  = data[var_names['WIND']].to_numpy()

    # Iterate through years and months to create separate files:
    for y in years:
        
        if (y == start_year) and (y != end_year):
            months = np.arange(start_month, 12 + 1)
        elif (y == end_year) and (y != start_year):
            months = np.arange(1, end_month + 1)
        elif (y == start_year) and (y == end_year):
            months = np.arange(start_month, end_month + 1)
        else:
            months = np.arange(1, 12 + 1)
        
        for m in months:
            
            os.makedirs(outdir, exist_ok=True)
            dst_name = os.path.join(outdir, f'{y:04d}-{m:02d}.nc')
        
            dst = nc.Dataset(dst_name, "w")

            indices = np.argwhere((site_dates.dt.year == y) & (site_dates.dt.month == m)).flatten()

            # PRECT
            precip_forc = pd.Series(Q_(prec_vals[indices], 
                                       src_units['PRECTmms']).to(dst_units['PRECTmms']).magnitude * scaling_factors['PRECTmms'],
                                    index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)
            

            # PSRF
            prs_forc = pd.Series(Q_(prs_vals[indices], 
                                       src_units['PSRF']).to(dst_units['PSRF']).magnitude * scaling_factors['PSRF'],
                                    index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)

            # FSDS
            fsds_forc = pd.Series(Q_(fsds_vals[indices], 
                                       src_units['FSDS']).to(dst_units['FSDS']).magnitude * scaling_factors['FSDS'],
                                    index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)
            

            # FLDS
            flds_forc = pd.Series(Q_(flds_vals[indices], 
                                       src_units['FLDS']).to(dst_units['FLDS']).magnitude * scaling_factors['FLDS'],
                                    index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)

            # RH
            q_forc = pd.Series(Q_(q_vals[indices], 
                                       src_units['RH']).to(dst_units['RH']).magnitude * scaling_factors['RH'],
                                    index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)

            # TBOT
            temp_forc = pd.Series(Q_(temp_vals[indices], 
                                    src_units['TBOT']).to(dst_units['TBOT']).magnitude * scaling_factors['TBOT'],
                                 index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)
            # WIND
            wind_forc = pd.Series(Q_(wind_vals[indices], 
                                    src_units['WIND']).to(dst_units['WIND']).magnitude * scaling_factors['WIND'],
                                 index=site_dates.iloc[indices]).resample(t_res).mean().to_numpy().astype(np.float64)
            
            # time hours since beginning of file
            time_forc = np.linspace(0, 
                                   (indices[-1] - indices[0]) * t_per_h, 
                                   indices[-1] - indices[-0], 
                                   dtype=np.float32)
            
            #print(time_forc)
            
            #exit()

            # dimensions
            dst.createDimension("scalar", 1)
            dst.createDimension("lon", 1)
            dst.createDimension("lat", 1)
            dst.createDimension("time", None) 


            # Attributes
            dst.setncattr("Forcings_generated_by", "Fernand Eloundou")
            dst.setncattr("on_date", datetime.datetime.today().strftime("%Y%m%d%H%M"))
            dst.setncattr("based_on", "data from ICOS portal") 
            dst.setncattr("used_for", "Singlepoint CLM 5.0")
            

            time = dst.createVariable("time", datatype=np.float32, dimensions=("time",))
            time.setncatts({"long_name": "observation time",
                            "units": f"hours since {y:04d}-{m:02d}-01 00:00:00", 
                            "calendar": "gregorian", 
                            "axis": "T"})
            
            # Time for 3-hour intervals
            dst.variables["time"][:] = time_forc[:]

            longxy = dst.createVariable("LONGXY", datatype=np.float32, dimensions=("lat", "lon"), 
                                        fill_value=np.float32(np.nan))
            longxy.setncatts({"long_name": "longitude", "units": "degrees E", "mode": "time-invariant"})     
            dst.variables["LONGXY"][:, :] = lon

            latixy = dst.createVariable("LATIXY", datatype=np.float32, dimensions=("lat", "lon"), 
                                        fill_value=np.float32(np.nan))
            latixy.setncatts({"long_name": "latitude", "units": "degrees N", "mode": "time-invariant"})            
            dst.variables["LATIXY"][:, :] = lat

            lone = dst.createVariable("LONE", datatype=np.float32, dimensions=("lat", "lon"), 
                                      fill_value=np.float32(np.nan))
            lone.setncatts({"long_name": "longitude of east edge", "units": "degrees E", "mode": "time-invariant"})            
            dst.variables["LONE"][:, :] = lon + lonbuffer

            latn = dst.createVariable("LATN", datatype=np.float32, dimensions=("lat", "lon"), 
                                      fill_value=np.float32(np.nan))
            latn.setncatts({"long_name": "latitude of north edge", "units": "degrees N", "mode": "time-invariant"})            
            dst.variables["LATN"][:, :] = lat + latbuffer

            lonw = dst.createVariable("LONW", datatype=np.float32, dimensions=("lat", "lon"), 
                                      fill_value=np.float32(np.nan))
            lonw.setncatts({"long_name": "longitude of west edge", "units": "degrees E", "mode": "time-invariant"})            
            dst.variables["LONW"][:, :] = lon - lonbuffer

            lats = dst.createVariable("LATS", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=np.float32(np.nan))
            lats.setncatts({"long_name": "latitude of south edge", "units": "degrees N", "mode": "time-invariant"})            
            dst.variables["LATS"][:, :] = lat - latbuffer

            prectmms = dst.createVariable("PRECTmms", datatype=np.float64,
                                          dimensions=("time", "lat", "lon",), 
                                          fill_value=np.float64(np.nan))
            prectmms.setncatts({"long_name": "Precipitation",
                                "units": dst_units["PRECTmms"], 
                                "missing_value": np.float64(np.nan),
                                "mode": "time-dependent"})
            
            dst.variables["PRECTmms"][:, :, :] = precip_forc[:]

            psrf = dst.createVariable("PSRF", datatype=np.float64,
                                      dimensions=("time", "lat", "lon",), 
                                      fill_value=np.float64(np.nan))
            psrf.setncatts({"long_name": "surface pressure at the lowest atm level (2m above ground)", 
                            "units": dst_units["PSRF"], 
                            "missing_value": np.float64(np.nan), 
                            "mode": "time-dependent"})
            dst.variables["PSRF"][:, :, :] = prs_forc[:]

            fsds = dst.createVariable("FSDS", datatype=np.float64,
                                      dimensions=("time", "lat", "lon",), 
                                      fill_value=np.float64(np.nan))
            fsds.setncatts({"long_name": "Downward shortwave radiation", 
                            "missing_value": np.float64(np.nan), 
                            "units": dst_units["FSDS"], 
                            "mode": "time-dependent"})
            
            dst.variables["FSDS"][:, :, :] = fsds_forc[:]

            flds = dst.createVariable("FLDS", datatype=np.float64,
                                      dimensions=("time", "lat", "lon",), 
                                      fill_value=np.float64(np.nan))
            flds.setncatts({"long_name": "Downward longwave radiation", 
                            "missing_value": np.float64(np.nan), 
                            "units": dst_units["FLDS"], 
                            "mode": "time-dependent"})
            
            dst.variables["FLDS"][:, :, :] = flds_forc[:]

            rh = dst.createVariable("RH", datatype=np.float64,
                                        dimensions=("time", "lat", "lon",), 
                                        fill_value=np.float64(np.nan))
            rh.setncatts({"long_name": "relative humidity at the lowest atm level (2m above ground)", 
                          "units": dst_units["RH"], 
                          "missing_value": np.float64(np.nan), 
                          "mode": "time-dependent"})
            
            dst.variables["RH"][:, :, :] = q_forc[:]

            tbot = dst.createVariable("TBOT", datatype=np.float64,
                                      dimensions=("time", "lat", "lon",), 
                                      fill_value=np.float64(np.nan))
            tbot.setncatts({"long_name": "temperature at the lowest atm level (2m above ground)", 
                            "units": dst_units["TBOT"], 
                            "missing_value": np.float64(np.nan), 
                            "mode": "time-dependent"})
            
            dst.variables["TBOT"][:, : , :] = temp_forc[:]

            wind = dst.createVariable("WIND", datatype=np.float64,
                                      dimensions=("time", "lat", "lon",), 
                                      fill_value=np.float64(np.nan))
            
            wind.setncatts({"long_name": "wind at the lowest atm level (2m above ground)", 
                            "units": dst_units["WIND"], 
                            "missing_value": np.float64(np.nan), 
                            "mode": "time-dependent"})
            
            dst.variables["WIND"][:, :, :] = wind_forc[:]


            edgen = dst.createVariable("EDGEN", np.float32, ("scalar",))
            edgen.setncatts({"long_name": "northern edge in atmospheric data", 
                             "units": "degrees N", 
                             "mode":"time-invariant"})
            
            edgee = dst.createVariable("EDGEE", np.float32, ("scalar",))
            edgee.setncatts({"long_name": "eastern edge in atmospheric data", 
                             "units": "degrees E", 
                             "mode": "time-invariant"})
            
            edges = dst.createVariable("EDGES", np.float32, ("scalar",))
            edges.setncatts({"long_name": "southern edge in atmospheric data", 
                             "units": "degrees N", 
                             "mode": "time-invariant"})
            
            edgew = dst.createVariable("EDGEW", np.float32, ("scalar",))
            edgew.setncatts({"long_name": "western edge in atmospheric data", 
                             "units": "degrees E", 
                             "mode": "time-invariant"})

            # location for site
            dst.variables["EDGEN"][:] = lat
            dst.variables["EDGES"][:] = lat
            dst.variables["EDGEE"][:] = lon
            dst.variables["EDGEW"][:] = lon