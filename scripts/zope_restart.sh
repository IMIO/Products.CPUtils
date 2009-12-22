#!/bin/bash
#if [ "$USER" != "zope" ]
#then
#    exec sudo -u zope $0 $@
#fi

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_restart"
for i in `cat /root/scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/cputils_scripts/zope_restart.py -i $i $*
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_restart"
