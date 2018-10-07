#!/bin/bash

# port=2000
# 
# if [ "$1" -gt 0 ] 2>/dev/null ;then
#     port=$1
# fi
#
# echo "http.server run on port:" $port

# echo ip address
ip -c -4 add | awk 'BEGIN{print "list ip add:"}/[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}..[0-9]{1,3}/{print " " $2}'

# run server
python3 fserver.py $@
