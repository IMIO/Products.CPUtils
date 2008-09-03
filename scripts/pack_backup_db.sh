#!/bin/bash
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_backup_db"
for i in `cat /root/scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/scripts/pack_backup_db.py $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of pack_backup_db"
