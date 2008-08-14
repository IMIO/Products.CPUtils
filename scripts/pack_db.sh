#!/bin/bash
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_db" >>/var/log/pack_db.log
for i in `cat /root/scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/scripts/pack_db.py $i >>/var/log/pack_db.log 2>&1
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_db" >>/var/log/pack_db.log
