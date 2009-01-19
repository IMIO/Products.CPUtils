#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of send_log"
/srv/python244/bin/python /root/cputils_scripts/send_log.py
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of send_log"
