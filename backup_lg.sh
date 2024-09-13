#!/bin/sh
umask 0002 # allow groups to rw
cd `dirname $0`;

. ./venv/bin/activate

log=`date +"./logs/lg_backup.%Y%m%d.%H%M"`

python3 lg_backup.py > $log 2>&1

