##### Install Nvidia Driver #####
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
curl -fsSL -o /usr/local/bin/donkey https://github.com/3XX0/donkey/releases/download/v1.1.0/donkey
curl -fsSL -o /usr/local/bin/extract-vmlinux https://raw.githubusercontent.com/torvalds/linux/master/scripts/extract-vmlinux
chmod +x /usr/local/bin/donkey /usr/local/bin/extract-vmlinux./NVIDIA-Linux-x86_64-410.104.run

#### Install Docker #####
apt-get install \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo apt-key add -apt-key fingerprint 0EBFCD88add-apt-repository \
  "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
docker run hello-world

#### Nvidia Docker ######
# If you have nvidia-docker 1.0 installed: we need to remove it and all existing GPU containers
docker volume ls -q -f driver=nvidia-docker | xargs -r -I{} -n1 docker ps -q -a -f volume={} | xargs -r docker rm -f
sudo apt-get purge -y nvidia-docker
# Add the package repositories
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | \
  sudo apt-key add -distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
# Install nvidia-docker2 and reload the Docker daemon configuration
sudo apt-get install -y nvidia-docker2
sudo pkill -SIGHUP dockerd
# Test nvidia-smi with the latest official CUDA image
docker run --runtime=nvidia --rm nvidia/cuda:9.0-base nvidia-smi

##### Exasol #####
sudo nvidia-docker run --name exasoldb -p 127.0.0.1:8899:8888 -p 127.0.0.1:6594:6583 --detach --privileged --stop-timeout 120 exasol/docker-db
sudo apt-get -y install python3-pip
sudo pip3 install pyexasol
