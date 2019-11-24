#!/bin/sh

set -e
set -u

HOSTNAME="$(hostname)"
VAGRANT_HOME="/home/vagrant"
SYNC_FOLDER="/provision-files"

if [ -z ${USE_HOME+x} ]
then
  echo "Copying $SYNC_FOLDER/$SRC/ to $DEST"
  rsync -r $SYNC_FOLDER/$SRC/ $DEST

  if [ -z ${USER+x} ]
  then
    echo ""
  else
    echo "Setting owner:group as $USER:$USER"
    chown -R $USER:$USER $DEST
  fi
else
  if [ "$USER" = "root" ]
  then
    USER_HOME="/root"
  else
    USER_HOME="/home/$USER"
  fi

  echo "Copying $SYNC_FOLDER/$SRC/ to $USER_HOME/$DEST"
  rsync -r $SYNC_FOLDER/$SRC/ $USER_HOME/$DEST
  echo "Setting owner:group as $USER:$USER"
  chown -R $USER:$USER $USER_HOME/$DEST
fi

echo "[SUCCESS]"
