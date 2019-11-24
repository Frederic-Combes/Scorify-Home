#!/bin/sh

set -e
set -u

HOSTNAME="$(hostname)"
VAGRANT_HOME="/home/vagrant"
SYNC_FOLDER="/provision-files"

if [ "$USER" = "root" ]
then
  USER_HOME="/root"
else
  USER_HOME="/home/$USER"
fi

export DEBIAN_FRONTEND=noninteractive

mkdir -p $USER_HOME/.ssh
cat $SYNC_FOLDER/.ssh/$KEY_NAME\_rsa.pub >> $USER_HOME/.ssh/authorized_keys
sort -u $USER_HOME/.ssh/authorized_keys > $USER_HOME/.ssh/authorized_keys.tmp
mv $USER_HOME/.ssh/authorized_keys.tmp $USER_HOME/.ssh/authorized_keys

echo "[SUCCESS] key $KEY_NAME authorized."
