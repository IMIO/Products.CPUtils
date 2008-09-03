#!/bin/bash
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_backup_db"
for i in `cat /root/cputils_scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/cputils_scripts/pack_backup_db.py $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of pack_backup_db"
