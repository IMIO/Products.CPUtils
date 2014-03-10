#!/bin/bash
#
# Script to call the pack of the instance's mount point with 
# the good parameters 
#
# © 2011 The CommunesPlone Project support@communesplone.org

declare -i port
days=7

for i in $(cat /srv/ZINSTANCES-P| grep ^[/srv] )
do 
    directory=$(echo $i | awk -F ";" '{print $1}')
    port=$(echo $i | awk -F ";" '{print $2}')
    
    # If port != 0 then we have a zeoserver
    if [ $port -ne 0 ]
    then
        cache=$(awk '/cache/ {print $1; exit}' "${directory}bin/zeoserver" | xargs dirname | sed s/eggs//)
        for j in $(ls -1 $directory/var/filestorage/*.fs)
        do
            storage=$(basename $j .fs)
            # Now we have all we need so we can call the python script
            if [ $storage != "Data" ]
            then
                eval ${directory}bin/python /srv/scripts/pack_zeo.py -c ${cache} -i ${directory} -s ${storage} -d ${days} -p ${port}
            fi
        done    
    fi

done

