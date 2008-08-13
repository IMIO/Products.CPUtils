#!/bin/bash
for i in `cat /root/scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/scripts/pack_db.py $i >>/root/scripts/pack.log 2>&1
done
