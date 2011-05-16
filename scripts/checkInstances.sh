#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of checkInstances"
for i in `cat /root/cputils_scripts/INSTANCES.txt`
do
/srv/python244/bin/python /root/cputils_scripts/checkInstances.py -i $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of checkInstances"
