#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of pack_backup_db"
/srv/python244/bin/python /root/cputils_scripts/send_log.py
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of pack_backup_db"
