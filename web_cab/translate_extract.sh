# /usr/bin/bash

# Temp directory
dirtmp=$(/usr/bin/uuidgen)
mkdir $dirtmp

# Generat translate file by py file
index=0
# Thx https://stackoverflow.com/a/2087038
find . -name '*.py' | sort | while read line; do
    pygettext -d msg -o ${dirtmp}/${index}.pot $line
    ((index=index+1))
done

### Concatenate all file
ls ${dirtmp} | sort | while read name_file; do
    # Copy only file from line 18
    num_line=0
    cat ${dirtmp}/${name_file} | while read line; do

        if [ $num_line -gt 16 ]
        then
            # Copy in 0.pot file
            echo $line >> ${dirtmp}/0.pot
        fi
        ((num_line++))
    done
done

# Delete double definition
msguniq ${dirtmp}/0.pot -o ${dirtmp}/0.pot

# Move new file
mv ${dirtmp}/0.pot msg/msg.pot

# Delete temporary directory
rm -fr $dirtmp

cd msg

# For each language we create or update translate file
ls -d */ | while read my_dir; do
    # Check if file exist
    if [ ! -f ${my_dir}LC_MESSAGES/msg.po ]; then
        msginit -l fr -i msg.pot -o ${my_dir}LC_MESSAGES/msg.po
    else
        msgmerge --update ${my_dir}LC_MESSAGES/msg.po msg.pot
    fi

done
