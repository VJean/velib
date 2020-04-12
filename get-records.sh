#!/bin/bash

DIR=$(dirname $0)
DL_DIR="${DIR}/records"
DL_FILE="${DIR}/last-velib.json"
MD5_FILE="${DIR}/check.md5"

echo_log() {
	echo $(date +"[%Y-%m-%dT%H-%M-%S] ") $1
}

test -d $DL_DIR || mkdir $DL_DIR

curl -o $DL_FILE -s 'https://opendata.paris.fr/api/records/1.0/search/?dataset=velib-disponibilite-en-temps-reel&timezone=Europe/Paris&rows=2000'

# quit if nothing new
test -f "${MD5_FILE}" && md5sum --status -c "${MD5_FILE}" && echo_log "nothing new" && exit 0

# let's build a csv file with the following headers :
# timestamp, station_name, lat, lon, mechanical, ebike, capacity, numdocksavailable, numbikesavailable
TIMESTAMP=$(cat $DL_FILE | jq '.records[0].record_timestamp')
NB_RECORDS=$(cat $DL_FILE | jq '.records | length')
cat $DL_FILE | jq -r '.records[] as $r | [$r.record_timestamp,$r.fields.name,$r.geometry.coordinates[0],$r.geometry.coordinates[1],$r.fields.mechanical,$r.fields.ebike,$r.fields.capacity,$r.fields.numdocksavailable,$r.fields.numbikesavailable] | @csv' >> ${DL_DIR}/$(date +"%Y%m%d")-velib-records.csv
echo_log "$NB_RECORDS records with timestamp ${TIMESTAMP}"

# compute checksum for the next pass
md5sum "${DL_FILE}" > "${MD5_FILE}"

