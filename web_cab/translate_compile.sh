# /usr/bin/bash
# Compile all translate files

cd msg

# For each language we compile translate file
ls -d */ | while read my_dir; do
    # Check if file exist
    if [ -f ${my_dir}LC_MESSAGES/msg.po ]; then
         msgfmt ${my_dir}LC_MESSAGES/msg.po -o ${my_dir}LC_MESSAGES/msg.mo
    fi

done
