#!/bin/bash
if [ -e zr_instances.log ]; then
   rm zr_instances.log
fi
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of checkInstances">>zr_instances.log
for i in `cat INSTANCES.txt`
do
/srv/python246/bin/python checkInstances.py -i $i >>zr_instances.log 2>&1
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of checkInstances">>zr_instances.log
