#!/bin/sh

set -e
set -u

HOSTNAME="$(hostname)"
VAGRANT_HOME="/home/vagrant"
SYNC_FOLDER="/provision-files"

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y apt-transport-https ca-certificates gnupg2
apt-get install -y curl wget rsync
apt-get install -y git vim
apt-get install -y python3 python3-pip pipenv software-properties-common make

echo "[SUCCESS] Base packages installed."
