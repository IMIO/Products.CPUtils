#!/bin/bash
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of test_db"
for i in `cat /root/cputils_scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/cputils_scripts/test_db.py $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of test_db"
