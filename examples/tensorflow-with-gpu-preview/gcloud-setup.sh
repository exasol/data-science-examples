#!/bin/bash

set -x -e -o pipefail -u
{
  ##### Install Nvidia Driver #####
  sudo echo "Install Nvidia Driver" >> /setup.log 

  curl -o NVIDIA-Linux-x86_64-410.104.run http://de.download.nvidia.com/tesla/410.104/NVIDIA-Linux-x86_64-410.104.run
  chmod +x NVIDIA-Linux-x86_64-410.104.run
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommends \
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
  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommends \
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
  sudo curl https://raw.githubusercontent.com/NVIDIA/nvidia-persistenced/master/init/systemd/nvidia-persistenced.service.template | sed 's/__USER__/root/' > /etc/systemd/system/nvidia-persistenced.service
  sudo systemctl enable nvidia-persistenced
  sudo systemctl start nvidia-persistenced
  
  #### Install Docker #####
  sudo echo "Install Docker" >> /setup.log

  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommends \
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
  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommends docker-ce docker-ce-cli containerd.io
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
  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommends nvidia-docker2
  sudo pkill -SIGHUP dockerd
  # Test nvidia-smi with the latest official CUDA image
  sudo docker run --runtime=nvidia --rm nvidia/cuda:9.0-base nvidia-smi

  ##### Install Python #####
  sudo echo "Install Python" >> /setup.log

  sudo DEBIAN_FRONTEND=noninteractive \
        apt-get install -yq --no-install-recommendspython3-pip
  sudo pip3 install pyexasol tensorboard tensorflow
  
  ##### Install Exasol #####
  sudo echo "Install Exasol" >> /setup.log

  git clone https://github.com/exasol/integration-test-docker-environment.git --branch enhancement/set_default_name_server_in_exaconf
  pushd integration-test-docker-environment
  /start-test-env spawn-test-environment --environment-name test --docker-runtime nvidia --database-port-forward 8888 --bucketfs-port-forward 6583 --db-mem-size 8GB --db-disk-size 8GB
  popd

  #### Download scripts ####
  sudo echo "Download scripts" >> /setup.log

  wget https://raw.githubusercontent.com/tkilias/data-science-examples/tensorflow-gpu-preview/examples/tensorflow-with-gpu-preview/system-status.sh
  sudo bash -x /system-status.sh &> status.log
  sudo cp status.log /

  sudo echo "Finished" >> /setup.log
} &> /tmp/setup_script.log
