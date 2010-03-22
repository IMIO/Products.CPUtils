#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of checkPOSKeyErrors"
for i in `cat /root/cputils_scripts/INSTANCES.txt`
do
/srv/python244/bin/python /root/cputils_scripts/checkPOSKeyErrors.py -i $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of checkPOSKeyErrors"
