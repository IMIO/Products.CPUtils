#!/bin/bash
for i in `cat INSTANCES.txt`
do /srv/python244/bin/python restore_db.py $i
done
