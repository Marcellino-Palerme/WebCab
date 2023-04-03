#!/bin/bash

# Copy conf
cp -n /temp_conf/conf.json /back/web_cab/conf/

# Run front of Web Cab
python /back/web_cab/background.py &

# start scheduler of update
# python /back/web_cab/update.py back &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
