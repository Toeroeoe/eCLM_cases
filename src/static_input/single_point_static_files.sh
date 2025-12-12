# Please update the script if any significant changes in the eCLM_static_files repositroy are made.

# User settings
## eCLM_static_files repository location
eclm_static_repo="eCLM_static-file-generator"

## site coordinates
### Example Aurade https://meta.icos-cp.eu/resources/stations/ES_FR-Aur
name="Aurade"
lat=43.54965
lon=1.106103

## Raw data paths
griddir="/p/scratch/cjibg31/jibg3105/CESMDataRoot/InputData/lnd/clm2/mappingdata/grids"

# MAIN CODE - DO NOT MODIFY BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING ##
latlon_buff=0.03
if (( $(echo "$lat > 0.0" | bc -l) )); then
    latlon_buff=$latlonbuff * -1
fi


## Set required environment variables 
### Number of grid cells in X and Y direction
export NX=1
export NY=1
export IMASK=0
export GRIDFILE="output/grids/SCRIPgrid_1x1_${name}_c`date +%y%m%d`.nc"

### Set bounding box coordinates
export S_LAT=$(echo "$lat - $latlon_buff" | bc -l)
export N_LAT=$(echo "$lat + $latlon_buff" | bc -l)
export W_LON=$(echo "$lon - $latlon_buff" | bc -l)
export E_LON=$(echo "$lon + $latlon_buff" | bc -l)

if [ -f $GRIDFILE ]; then
    echo "Grid file $GRIDFILE already exists. Skipping grid generation."
else
    echo "Generating grid file $GRIDFILE ..."
    python eCLM_static-file-generator/mkmapgrids/mkscripgrid.py
fi

if [ "$(ls output/maps/*${name}*_c`date +%y%m%d`.nc | wc -l)" -ge 17 ]; then
    echo "Map files for site $name already exist. Skipping map generation."

else 
    echo "Generating map files for site $name ..."
    jobid=$(sbatch \
        --parsable \
        --wait \
        eCLM_static-file-generator/mkmapdata/runscript_mkmapdata.sh \
            $name \
            $GRIDFILE \
            $griddir)
    mv PET*.Log output/logs/
fi

export MAPFILE="output/maps/map_0.5x0.5_AVHRR_to_${name}_nomask_aave_da_c`date +%y%m%d`.nc"

if [ -f "output/domains/domain.lnd.${name}_${name}.`date +%y%m%d`.nc" ]; then
    echo "Domain file for site $name already exists. Skipping domain generation."
else 
    echo "Generating domain file for site $name ..."
    ifort \
        -o eCLM_static-file-generator/gen_domain_files/gen_domain eCLM_static-file-generator/gen_domain_files/src/gen_domain.F90 \
        -qmkl \
        -lnetcdff \
        -lnetcdf 
    ./eCLM_static-file-generator/gen_domain_files/gen_domain \
        -m $MAPFILE \
        -o $name \
        -l $name
    mv domain.lnd.${name}_${name}.`date +%y%m%d`.nc output/domains/domain.lnd.${name}_${name}.`date +%y%m%d`.nc
    mv domain.ocn.${name}_${name}.`date +%y%m%d`.nc output/domains/domain.ocn.${name}_${name}.`date +%y%m%d`.nc
    rm domain.ocn.${name}.`date +%y%m%d`.nc
fi

export CDATE=`date +%y%m%d`
export CSMDATA="/p/scratch/cjibg31/jibg3105/CESMDataRoot/InputData/"

if [ -f "output/surf/surfdata_${name}_*`date +%y%m%d`.nc" ]; then
    echo "Surface file for site $name already exists. Skipping surface generation."
else 
    echo "Generating surface file for site $name ..."
    

    echo $name $CDATE $CSMDATA

    ./eCLM_static-file-generator/mksurfdata/mksurfdata.pl \
        -r usrspec \
        -usr_mapdir output/maps/ \
        -usr_gname $name \
        -usr_gdate $CDATE \
        -l $CSMDATA \
        -allownofile \
        -y 2000 \
        -crop \
        #-hirespft

    mv surfdata_* output/surf/
fi
