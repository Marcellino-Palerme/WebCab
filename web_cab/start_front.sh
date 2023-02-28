#!/bin/bash

# Copy conf
cp -n /temp_conf/conf.json /web-cab/web_cab/conf/

# Run front of Web Cab
nohup streamlit run --browser.gatherUsageStats false /web-cab/web_cab/1_📥_upload.py &

# start scheduler of update
nohup python /web-cab/web_cab/update.py front &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
