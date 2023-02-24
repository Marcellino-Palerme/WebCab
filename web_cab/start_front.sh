#!/bin/bash

# Copy conf
cp -n /temp_conf/conf.json web_cab/conf/

# Run front of Web Cab
streamlit run --browser.gatherUsageStats false web_cab/1_📥_upload.py &

# start scheduler of update
python web_cab/update.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
