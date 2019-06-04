#!/bin/bash

set -x -e -o pipefail -u
{
  ##### Install Nvidia Driver #####
  sudo echo "Install Nvidia Driver" >> /setup.log 

  curl -o NVIDIA-Linux-x86_64-410.104.run http://de.download.nvidia.com/tesla/410.104/NVIDIA-Linux-x86_64-410.104.run
  chmod +x NVIDIA-Linux-x86_64-410.104.run
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
                            cpp=4:7.3.0-3ubuntu2 \
                            cpp-7=7.3.0-16ubuntu3 \
                            g++=4:7.3.0-3ubuntu2 \
                            g++-7=7.3.0-16ubuntu3 \
                            gcc=4:7.3.0-3ubuntu2 \
                            gcc-7=7.3.0-16ubuntu3 \
                            gcc-7-base=7.3.0-16ubuntu3 \
                            libasan4=7.3.0-16ubuntu3 \
                            libcilkrts5=7.3.0-16ubuntu3 \
                            libgcc-7-dev=7.3.0-16ubuntu3 \
                            libstdc++-7-dev=7.3.0-16ubuntu3 \
                            libubsan0=7.3.0-16ubuntu3
  sudo apt-mark hold cpp cpp-7 g++ g++-7 gcc gcc-7 gcc-7-base libasan4 \
                    libcilkrts5 libgcc-7-dev libstdc++-7-dev libubsan0
  sudo dpkg --add-architecture i386
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends \
                          apt-utils \
                          build-essential \
                          ca-certificates \
                          curl \
                          kmod \
                          libc6:i386 \
                          libelf-dev
  sudo curl -fsSL -o /usr/local/bin/donkey https://github.com/3XX0/donkey/releases/download/v1.1.0/donkey
  sudo curl -fsSL -o /usr/local/bin/extract-vmlinux https://raw.githubusercontent.com/torvalds/linux/master/scripts/extract-vmlinux
  sudo chmod +x /usr/local/bin/donkey /usr/local/bin/extract-vmlinux
  ./NVIDIA-Linux-x86_64-410.104.run --silent

  #### Install Docker #####
  sudo echo "Install Docker" >> /setup.log

  sudo apt-get install -y --no-install-recommends \
          apt-transport-https \
          ca-certificates \
          curl \
          gnupg-agent \
          software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo apt-key fingerprint 0EBFCD88
  sudo add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io
  sudo docker run hello-world

  #### Nvidia Docker ######
  sudo echo "Install Nvidia Docker" >> /setup.log

  # Add the package repositories
  curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list
  sudo apt-get update
  # Install nvidia-docker2 and reload the Docker daemon configuration
  sudo apt-get install -y nvidia-docker2
  sudo pkill -SIGHUP dockerd
  # Test nvidia-smi with the latest official CUDA image
  sudo docker run --runtime=nvidia --rm nvidia/cuda:9.0-base nvidia-smi

  ##### Install Exasol #####
  sudo echo "Install Exasol" >> /setup.log

  wget https://raw.githubusercontent.com/tkilias/data-science-examples/tensorflow-gpu-preview/examples/tensorflow-with-gpu-preview/EXAConf
  sudo mkdir -p /exa/{etc,data/storage}
  sudo cp EXAConf /exa/etc/EXAConf
  SIZE="$((45*1073741824))"
  sudo dd if=/dev/zero of=/exa/data/storage/dev.1 bs=1 count=1 seek=$SIZE
  sudo chmod +rw /exa
  sudo nvidia-docker run --name exasoldb -p 8888:8888 -p 6583:6583 -v /exa:/exa --detach --privileged --stop-timeout 120 --restart always exasol/docker-db

  ##### Install Python #####
  sudo echo "Install Python" >> /setup.log

  sudo apt-get -y install python3-pip
  sudo pip3 install pyexasol

  #### Download scripts ####
  sudo echo "Download scripts" >> /setup.log

  wget https://raw.githubusercontent.com/tkilias/data-science-examples/tensorflow-gpu-preview/examples/tensorflow-with-gpu-preview/system-status.sh
  sudo cp system-status.sh /

  #### Finish Setup #####
  sudo echo "Wait for Exasol" >> /setup.log

  sleep 180 # Wait for database to startup
  sudo bash -x /system-status.sh &> status.log
  sudo cp status.log /

  sudo echo "Finished" >> /setup.log
} &> /tmp/setup_script.log
