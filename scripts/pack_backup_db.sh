#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_backup_db"
for i in `cat ./INSTANCES.txt`
do
    if [ "$1" = "-F" ];
    then
      /srv/python246/bin/python ./pack_backup_db.py -i $i -F
    else
      /srv/python246/bin/python ./pack_backup_db.py -i $i
    fi
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of pack_backup_db"
