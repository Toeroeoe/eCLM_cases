import os
import datetime
import pytz
import numpy as np
import netCDF4 as nc
import pandas as pd


# Settings
infile: str = '/home/fernand/Downloads/flxnet_sites/SE-Svb_ICOS_2014-2020_beta-3/6h_se_svb_met.csv'
outdir: str = '/home/fernand/JURECA/CLM5_DATA/inputdata/atm/datm7/trial_22/SE-Svb/local/'

var_names: dict[str, str | None] = {'PRECTmms': 'P', 
                                    'PSRF': 'PA', 
                                    'FSDS': 'SW_IN', 
                                    'FLDS': 'LW_IN', 
                                    'RH': 'RH', 
                                    'TBOT': 'TA', 
                                    'WIND': 'WS'}

src_units: dict[str, str | None] = {'PRECTmms': 'mm/30min',
                                    'PSRF': 'kPa',
                                    'FSDS': 'W/m^2',
                                    'FLDS': 'W/m^2',
                                    'RH': '%',
                                    'TBOT': '°C',
                                    'WIND': 'm/s'}

dst_units: dict[str, str | None] = {'PRECTmms': 'mm/s',
                                    'PSRF': 'Pa',
                                    'FSDS': 'W/m^2',
                                    'FLDS': 'W/m^2',
                                    'RH': '%',
                                    'TBOT': 'K',
                                    'WIND': 'm/s'}

time_col: str = 'TIMESTAMP_START'
time_format: str = '%Y-%m-%d %H:%M:%S'
start_year: int = 2014
end_year: int = 2019
start_month: int = 1
end_month: int = 12


def get_dates_from_file(df: pd.DataFrame) -> np.ndarray:   
        return np.array([pytz.utc.localize(date) for date in df.index])
    
    
def get_index_from_dates(dates: np.ndarray, 
                         year: int, 
                         month: int) -> tuple[int, int]:
        
        start = np.where(dates == datetime.datetime(year, month, 1, 0, 0, tzinfo=datetime.timezone.utc))[0][0]
        
        if month == 12:
            if year == years[-1]:
                end = len(dates)
            else:
                end = np.where(dates == datetime.datetime(year + 1, 1, 1, 0, 0, tzinfo=datetime.timezone.utc))[0][0]
        else:
            end = np.where(dates == datetime.datetime(year, month+1, 1, 0, 0, tzinfo=datetime.timezone.utc))[0][0]
        return (start, end)


if __name__ == "__main__":

    # reading in data
    data = pd.read_csv(infile, na_values=["-9999", "-9999.0"])

    # Convert 'TIMESTAMP_START' to datetime format and set as index
    data[time_col] = pd.to_datetime(data[time_col], format=time_format)
    data.set_index(time_col, inplace=True)

    site_dates = get_dates_from_file(data)
    years = np.arange(start_year, end_year + 1)

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
        
        if y == start_year:
            months = np.arange(start_month, 12 + 1)
        elif y == end_year:
            months = np.arange(1, end_month + 1)
        else:
            months = np.arange(1, 12 + 1)
        
        for m in months:
            
            os.makedirs(outdir, exist_ok=True)
            dst_name = os.path.join(outdir, f'{y:04d}-{m:02d}.nc')
        
            dst = nc.Dataset(dst_name, "w")

            try:
                # get indices
                index_s, index_e = get_index_from_dates(site_dates, y, m)

                # PRECT [mm/s]
                precip_forc = np.array(prec_vals[index_s:index_e])
                precip_forc[np.isnan(precip_forc)]= 1e+36

                # PSRF [Pa]
                if prs_unit == 'KPa':
                    prs_forc = np.array(prs_vals[index_s:index_e] * 1000.0)
                    prs_forc[np.isnan(prs_forc)]= 1e+36
                if prs_unit == 'MPa':
                    prs_forc = np.array(prs_vals[index_s:index_e] * 1000000.0)
                    prs_forc[np.isnan(prs_forc)]= 1e+36

                #  FSDS [W / m^2]
                fsds_forc = np.array(fsds_vals[index_s:index_e])
                fsds_forc[np.isnan(fsds_forc)]= 1e+36

                #  FLDS [W / m^2]
                flds_forc = np.array(flds_vals[index_s:index_e])
                flds_forc[np.isnan(flds_forc)]= 1e+36

                # RH [%]
                if q_unit == '%':
                    q_forc = np.array(q_vals[index_s:index_e])
                    q_forc[np.isnan(q_forc)]= 1e+36
                if q_unit == 'portion':
                    q_forc = np.array(q_vals[index_s:index_e] * 100.0)
                    q_forc[np.isnan(q_forc)]= 1e+36


                # TBOT [K]
                temp_forc = np.array(temp_vals[index_s:index_e])
                temp_forc[np.isnan(temp_forc)]= 1e+36

                # WIND [m/s]
                wind_forc = np.array(wind_vals[index_s:index_e])
                wind_forc[np.isnan(wind_forc)]= 1e+36

                # time hours since beginning of file
                time_forc = np.linspace(0, (index_e - index_s) * 6, (index_e - index_s), endpoint=False)


                # dimensions
                dst.createDimension("scalar", 1)
                dst.createDimension("lon", 1)
                dst.createDimension("lat", 1)
                dst.createDimension("time", None) #len(time_forc))


                # Attributes
                dst.setncattr("Forcings_generated_by", "Fernand Eloundou")
                dst.setncattr("on_date", datetime.datetime.today().strftime("%Y%m%d%H%M"))
                dst.setncattr("based_on", "data from ICOS portal") 
                dst.setncattr("used_for", "Singlepoint CLM 5.0")

                time = dst.createVariable("time", datatype=np.float32, dimensions=("time",))
                time.setncatts({'long_name': u"observation time",
                                'units': u"hours since " + str(y) + "-" + str(m).zfill(2) + "-01 00:00:00", 
                                "calendar": u"gregorian", "axis": u"T"})
                # Time for 3-hour intervals
                dst.variables["time"][:] = time_forc[:]

                longxy = dst.createVariable("LONGXY", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                longxy.setncatts({"long_name": "longitude", "units": "degrees E", "mode": "time-invariant"})     
                dst.variables["LONGXY"][:, :] = 19.7745

                latixy = dst.createVariable("LATIXY", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                latixy.setncatts({"long_name": "latitude", "units": "degrees N", "mode": "time-invariant"})            
                dst.variables["LATIXY"][:, :] = 64.25611

                lone = dst.createVariable("LONE", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                lone.setncatts({"long_name": "longitude of east edge", "units": "degrees E", "mode": "time-invariant"})            
                dst.variables["LONE"][:, :] = 19.7845

                latn = dst.createVariable("LATN", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                latn.setncatts({"long_name": "latitude of north edge", "units": "degrees N", "mode": "time-invariant"})            
                dst.variables["LATN"][:, :] = 64.26611

                lonw = dst.createVariable("LONW", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                lonw.setncatts({"long_name": "longitude of west edge", "units": "degrees E", "mode": "time-invariant"})            
                dst.variables["LONW"][:, :] = 19.7645

                lats = dst.createVariable("LATS", datatype=np.float32, dimensions=("lat", "lon"), 
                                            fill_value=9.96921e+36)
                lats.setncatts({"long_name": "latitude of south edge", "units": "degrees N", "mode": "time-invariant"})            
                dst.variables["LATS"][:, :] = 64.24611


                prectmms = dst.createVariable("PRECTmms", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                prectmms.setncatts({"long_name": "Precipitation",'units': "mm/s", "missing_value": 1e+36, "mode": "time-dependent"})
                dst.variables["PRECTmms"][:, :, :] = precip_forc[:]

                psrf = dst.createVariable("PSRF", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                psrf.setncatts({"long_name":"surface pressure at the lowest atm level (2m above ground)", 'units': "Pa", "missing_value": 1e+36, "mode": "time-dependent"})
                dst.variables["PSRF"][:, :, :] = prs_forc[:]

                fsds = dst.createVariable("FSDS", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                fsds.setncatts({"long_name": "Downward shortwave radiation", "missing_value": 1e+36, 'units': "W/m^2", "mode": "time-dependent"})
                dst.variables["FSDS"][:, :, :] = fsds_forc[:]

                flds = dst.createVariable("FLDS", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                flds.setncatts({"long_name": "Downward longwave radiation", "missing_value": 1e+36, 'units': "W/m^2", "mode": "time-dependent"})
                dst.variables["FLDS"][:, :, :] = flds_forc[:]

                rh = dst.createVariable("RH", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                rh.setncatts({"long_name":"relative humidity at the lowest atm level (2m above ground)", 'units': "%", "missing_value": 1e+36, "mode": "time-dependent"})
                dst.variables["RH"][:, :, :] = q_forc[:]

                tbot = dst.createVariable("TBOT", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                tbot.setncatts({"long_name":"temperature at the lowest atm level (2m above ground)", 'units': "K", "missing_value": 1e+36, "mode": "time-dependent"})
                dst.variables["TBOT"][:, : , :] = temp_forc[:]

                wind = dst.createVariable("WIND", datatype=np.float64,
                                            dimensions=("time", "lat", "lon",), 
                                            fill_value=1e+36)
                wind.setncatts({"long_name":"wind at the lowest atm level (2m above ground)", 'units': "m/s", "missing_value": 1e+36, "mode": "time-dependent"})
                dst.variables["WIND"][:, :, :] = wind_forc[:]

                #zbot = dst.createVariable("ZBOT", datatype=np.float32,
                #                            dimensions=("time", "lat", "lon",), 
                #                            fill_value=1e+36)
                #zbot.setncatts({"long_name":"observation height", "missing_value": 1e+36, "unit": "m a.s.l.", "mode": "time-invariant"})
                #dst.variables["ZBOT"][:, :, :] = 2.0 


                edgen = dst.createVariable("EDGEN", np.float32, ("scalar",))
                edgen.setncatts({"long_name":"northern edge in atmospheric data", "units": "degrees N", "mode":"time-invariant"})
                edgee = dst.createVariable("EDGEE", np.float32, ("scalar",))
                edgee.setncatts({"long_name":"eastern edge in atmospheric data", "units": "degrees E", "mode":"time-invariant"})
                edges = dst.createVariable("EDGES", np.float32, ("scalar",))
                edges.setncatts({"long_name":"southern edge in atmospheric data", "units": "degrees N", "mode":"time-invariant"})
                edgew = dst.createVariable("EDGEW", np.float32, ("scalar",))
                edgew.setncatts({"long_name":"western edge in atmospheric data", "units": "degrees E", "mode":"time-invariant"})

                # location for site
                dst.variables["EDGEN"][:] = 64.25611
                dst.variables["EDGES"][:] = 64.25611
                dst.variables["EDGEE"][:] = 19.7745
                dst.variables["EDGEW"][:] = 19.7745

            except:
                print(f"skipped month {m} in year {y}")