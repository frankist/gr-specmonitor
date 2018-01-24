#!/bin/bash
set -e # exist if there is any fail
cd ..
WORKSPACE_PATH=$(readlink -f ./)
FRAMEWORK_PATH=$(readlink -f ./python)

# build module
mkdir -p build
cd build
cmake ../
make -j4
sudo make install
sudo ldconfig
cd ../

# make tmp folder
mkdir -p tmp

# pass framework to python path
echo export PYTHONPATH="${PYTHONPATH}:"${FRAMEWORK_PATH} >>~/.bashrc
source ~/.bashrc

# install required dependencies
sudo apt-get update
## pip
sudo apt install -y python-pip
pip install --upgrade pip
sudo apt install -y python3-pip
pip3 install --upgrade pip
## tensorflow
sudo -H pip install tensorflow
sudo -H pip3 install tensorflow
sudo apt install python-opencv
# sudo apt install python3-opencv
sudo -H pip install future
sudo apt install python-yaml
sudo pip install configparser
sudo pip install matplotlib

# install luigi
sudo -H pip install luigi
sudo -H pip install scipy
sudo -H pip install Pillow
sudo -H pip install jsonpickle

# install darkflow
sudo -H pip install cython
sudo -H pip3 install cython
cd ~
git clone https://github.com/frankist/darkflow.git
cd darkflow
sudo pip install .

# check if installation is correct
python -c "import tensorflow"
python3 -c "import tensorflow"
python -c "import darkflow"
