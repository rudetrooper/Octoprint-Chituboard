#!/usr/bin/env bash

# Exit on error
set -euo pipefail

# filename: Chituboard.sh
# modified version of Kenzillla's Mariner+Samba Auto-Installer

function info { echo -e "\e[32m[info] $*\e[39m"; }
function warn  { echo -e "\e[33m[warn] $*\e[39m"; }
function error { echo -e "\e[31m[error] $*\e[39m"; exit 1; }

if ! [ "$(id -u)" = 0 ]; then
    warn "This script needs to be run as root." >&2
    exit 1
fi

info
info "Welcome to Octoprint+Samba Auto-Installer!"
sleep .1
info "..."

sleep 1

# Checks the base of the dir this script is being run in such as /home/username/Chituboard.sh 
# This sets the var to the last directory in the file path.
ASSUMED_USER=$(basename "$(pwd)") 
DEFAULT_USER="pi"

info "File is being run in $(pwd)"
info "Which user account should the be installed in that contains your octoprint config?  The user may be ${ASSUMED_USER}."
info "Please confirm this below or choose another user."

read -r user_input

USER="${user_input:-${DEFAULT_USER}}"

info "User is: ${USER}"

info
info "Setting up Chituboard prerequisites"
echo "dtoverlay=dwc2,dr_mode=peripheral" >> /boot/config.txt
echo "enable_uart=1" >> /boot/config.txt
sudo sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt
echo -n " modules-load=dwc2" >> /boot/cmdline.txt

# Setup 4 GB container file to for storing uploaded files
info
info "Setting up Pi-USB (4GB); this could take several minutes"
sudo dd bs=1M if=/dev/zero of=/piusb.bin count=4096
sudo mkdosfs /piusb.bin -F 32 -I
# Create the mount point for the container file
sudo mkdir /home/"${USER}"/.octoprint/uploads/resin
echo "/piusb.bin            /home/${USER}/.octoprint/uploads/resin  vfat    users,uid=${USER},gid=${USER},umask=000   0       2 " >> /etc/fstab

sudo mount -a

sudo sed -i 's/exit 0//g' /etc/rc.local

echo '/bin/sleep 5
modprobe g_mass_storage file=/piusb.bin removable=1 ro=0 stall=0
exit 0' >> /etc/rc.local

sudo systemctl stop serial-getty@ttyS0
sudo systemctl disable serial-getty@ttyS0

info ""
info "Setting up Sambashare; this could take a long time"
sudo apt-get install samba winbind -y

read -r -p "Enter a short description of your printer, like the model: "  model
echo "[USB_Share]
comment = $model
path = /home/${USER}/.octoprint/uploads/resin/
browseable = Yes
writeable = Yes
only guest = no
create mask = 0777
directory mask = 0777
public = yes
read only = no
force user = root
force group = root" >> /etc/samba/smb.conf

info ""

while true
do
    warn "Confirm your disk setup looks correct before rebooting"
    df -h
    
    read -r -p "Reboot now? [Y/n] " input

    case $input in
        [yY][eE][sS]|[yY])
    warn "Rebooting in 5 seconds"
    sleep 5
    sudo reboot
    break
    ;;
        [nN][oO]|[nN])
    break
            ;;
        *)
    warn "Invalid input..."
    esac
done

