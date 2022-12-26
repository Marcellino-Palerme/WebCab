# /usr/bin/bash

# Thx stackoverflow
# https://stackoverflow.com/a/73590099 and https://stackoverflow.com/a/42876846
if [ "$USER" = "root" ]; then
    echo "(1) already root"
else
    sudo -k # make sure to ask for password on next sudo
    if sudo true; then
        echo "(2) correct password"
    else
        echo "(3) wrong password"
        exit 1
    fi
fi

read -p "Enter token gitlab : " token
read -p "Enter administrator login : " name
read -p "Enter administrator email : " email
read -p "Enter site email: " site_email
read -sp "Enter site email password: " site_email_pwd
read -p "Enter site email server: " site_email_sv

sudo podman pod create -p 8501:8501 -n pod_wc

# Thx stackoverflow
# https://stackoverflow.com/a/10497540
# Generate password of database
pwd_db=$( dd if=/dev/urandom bs=50 count=1|base64)


# Create container of database
sudo podman run -d --name pg_wc --pod=pod_wc -e POSTGRES_PASSWORD=$pwd_db postgres

## Define configuration file
# administrator configuration
conf='{"login":"'
conf=$conf${name}
temp='","email":"'
conf=$conf$temp
conf=$conf${email}

# Site Email configuration
temp='","sender_email":"'
conf=$conf$temp
conf=$conf${site_email}
temp='","pwd_email":"'
conf=$conf$temp
conf=$conf${site_email_pwd}
temp='","smtp_server":"'
conf=$conf$temp
conf=$conf${site_email_sv}

# Database configuration
temp='","db": {"database":"postgres", "user": "postgres", "password":"'
conf=$conf$temp
conf=$conf${pwd_db}
temp='", "host":"localhost", "port": "5432"}}'
conf=$conf$temp

# Create image for web_cab
sudo podman build -t web_cab --label TOKEN=$token -<<EOF
FROM python:slim
# install system librairies
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y git
RUN apt install -y libzbar-dev
RUN apt install -y tar
RUN apt install -y wget
RUN apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
RUN apt-get install -y libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev
RUN apt-get install -y libgtk2.0-dev libgtk-3-dev tk
RUN apt-get install -y libpng-dev libjpeg-dev libopenexr-dev libtiff-dev
RUN apt install -y libwebp-dev

### Get two projects
RUN git clone https://oauth2:${token}@forgemia.inra.fr/demecologie/web-cab.git
RUN git clone https://oauth2:${token}@forgemia.inra.fr/demecologie/cab.git

### Install all modules
RUN pip install -U pip
RUN pip install poetry

# create requirements file for web-cab
RUN cd web-cab && poetry export -f requirements.txt --without-hashes --output requirements.txt
RUN sed -i /cab/d  web-cab/requirements.txt

RUN pip install -r cab/requirements.txt
RUN pip install -r web-cab/requirements.txt

# Install cab
RUN cd cab && python setup.py install

RUN mkdir web-cab/web_cab/conf
RUN echo '${conf}' >> web-cab/web_cab/conf/conf.json

WORKDIR web-cab

# Command to run web-cab
CMD streamlit run --browser.gatherUsageStats false web_cab/upload.py

EOF

# Create container of web_cab
sudo podman run -d --name ct_web_cab --pod=pod_wc web_cab
