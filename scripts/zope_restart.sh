#!/bin/bash
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_restart"
for i in `cat /root/scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/scripts/zope_restart.py $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_restart"
