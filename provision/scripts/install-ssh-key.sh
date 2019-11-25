#!/bin/sh

set -e
set -u

HOSTNAME="$(hostname)"
VAGRANT_HOME="/home/vagrant"
SYNC_FOLDER="/provision-files"

export DEBIAN_FRONTEND=noninteractive

# Install SSH key for github
cp $SYNC_FOLDER/.ssh/$KEY_NAME\_rsa $VAGRANT_HOME/.ssh/$KEY_NAME\_rsa || :
cp $SYNC_FOLDER/.ssh/$KEY_NAME\_rsa.pub $VAGRANT_HOME/.ssh/$KEY_NAME\_rsa.pub || :

# Setup SSH config file
touch $VAGRANT_HOME/.ssh/config
sed -i -e "/## BEGIN $KEY_NAME KEY/,/## END $KEY_NAME KEY/d" $VAGRANT_HOME/.ssh/config

echo "## BEGIN $KEY_NAME KEY" >> $VAGRANT_HOME/.ssh/config
cat $SYNC_FOLDER/.ssh/$KEY_NAME.config >> $VAGRANT_HOME/.ssh/config
echo "## END $KEY_NAME KEY" >> $VAGRANT_HOME/.ssh/config

# Fix rigths for SSH related files
chown -R vagrant:vagrant $VAGRANT_HOME/.ssh/
chmod 0600 $VAGRANT_HOME/.ssh/*
chmod 0644 $VAGRANT_HOME/.ssh/config
chmod 0700 $VAGRANT_HOME/.ssh

echo "[SUCCESS] Private key $KEY_NAME added and configured."
