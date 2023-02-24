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
read -p "Enter where save configuration: " path_conf
read -p "Enter where save inputs: " path_inputs
read -p "Enter administrator login : " name
read -p "Enter administrator email : " email
read -p "Enter site email: " site_email
read -p "Enter site email server: " site_email_sv
read -sp "Enter site email password: " site_email_pwd

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

# Create image for web_cab front-end
sudo podman build -t web_cab_front --label TOKEN=$token -<<EOF
FROM python:slim
# install system librairies
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y git
RUN apt install -y procps

### Get two projects
RUN git clone https://oauth2:${token}@forgemia.inra.fr/demecologie/web-cab.git

### Install all modules
RUN pip install -U pip
RUN pip install poetry

# create requirements file for web-cab
RUN cd web-cab && poetry export -f requirements.txt --without-hashes --output requirements.txt

RUN pip install -r web-cab/requirements.txt

RUN mkdir /temp_conf
RUN echo '${conf}' >> /temp_conf/conf.json

RUN mkdir web-cab/web_cab/conf
RUN echo '${conf}' >> web-cab/web_cab/conf/conf.json

WORKDIR web-cab

# Command to run web-cab
CMD cp -n /temp_conf/conf.json web_cab/conf/ & python web_cab/update.py & streamlit run --browser.gatherUsageStats false web_cab/1_📥_upload.py

EOF

# Create image for web_cab back-end
sudo podman build -t web_cab_back --label TOKEN=$token -<<EOF
FROM python:slim
# install system librairies
RUN apt update -y
RUN apt upgrade -y
RUN apt install -y git
RUN apt install -y libzbar-dev
RUN apt-get install -y libavcodec-dev libavformat-dev libswscale-dev
RUN apt-get install -y libgstreamer-plugins-base1.0-dev libgstreamer1.0-dev
RUN apt-get install -y libgtk2.0-dev libgtk-3-dev tk
RUN apt-get install -y libpng-dev libjpeg-dev libopenexr-dev libtiff-dev
RUN apt install -y libwebp-dev
RUN apt install -y procps

### Get two projects
# Get Cab
RUN git clone https://oauth2:${token}@forgemia.inra.fr/demecologie/cab.git
# Get partial web-cab
RUN mkdir back
RUN cd back && git init
RUN cd back && git config init.defaultBranch main
RUN cd back && git config core.sparseCheckout true
RUN cd back && git config pull.rebase false
RUN cd back && git remote add -f origin https://oauth2:${token}@forgemia.inra.fr/demecologie/web-cab.git
RUN cd back && echo "web_cab/my_email.py" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/connect.py" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/background.py" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/update.py" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/translate.py" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/msg/fr/LC_MESSAGES/msg.mo" >> .git/info/sparse-checkout
RUN cd back && echo "web_cab/msg/en/LC_MESSAGES/msg.mo" >> .git/info/sparse-checkout
RUN cd back && echo "pyproject.toml" >> .git/info/sparse-checkout
RUN cd back && echo "poetry.lock" >> .git/info/sparse-checkout
RUN cd back && git pull origin main



### Install all modules
RUN pip install -U pip
RUN pip install poetry
# create requirements file for web-cab
RUN cd back && poetry export -f requirements.txt --without-hashes --only back --output requirements.txt
RUN pip install -r cab/requirements.txt
RUN pip install -r back/requirements.txt

# Install cab
RUN cd cab && python setup.py install

RUN mkdir /temp_conf
RUN echo '${conf}' >> /temp_conf/conf.json

WORKDIR back

# Command to run web-cab
CMD cp -n /temp_conf/conf.json web_cab/conf/ & python web_cab/update.py & python web_cab/background.py

EOF

# Create container of web_cab front-end
sudo podman run -d --name ct_web_cab_f --pod=pod_wc -v ${path_inputs}:/web-cab/web_cab/temp -v ${path_conf}:/web-cab/web_cab/conf web_cab_front
# Create container of web_cab back-end
sudo podman run -d --name ct_web_cab_b --pod=pod_wc -v ${path_inputs}:/back/web_cab/temp  -v ${path_conf}:/back/web_cab/conf  web_cab_back
