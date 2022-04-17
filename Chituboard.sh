#!/usr/bin/env bash

# filename: Chituboard.sh
# modified version of Kenzillla's Mariner+Samba Auto-Installer

function info { echo -e "\e[32m[info] $*\e[39m"; }
function warn  { echo -e "\e[33m[warn] $*\e[39m"; }
function error { echo -e "\e[31m[error] $*\e[39m"; exit 1; }

if ! [ "$(id -u)" = 0 ]; then
    warn "This script needs to be run as root." >&2
    exit 1
fi

# check if the reboot flag file exists. 
# We created this file before rebooting.
if [ ! -f ./resume-Chituboard ]; then
    warn "running script for the first time.."
    
    # run your scripts here
    info
    info "Welcome to Octoprint+Samba Auto-Installer!"
    sleep .1
    info "..."

    sleep 1
# remove this part, octoprint install is already expanded filesystem

    warn "It is a good idea to change your password from the default"
    while true
    do
        read -r -p "Change now? [Y/n] " input
    
        case $input in
            [yY][eE][sS]|[yY])
        info
        echo "$(passwd pi)"
        break
        ;;
            [nN][oO]|[nN])
        break
                ;;
            *)
        warn "Invalid input..."
        esac
    done

    # create a flag file to check if we are resuming from reboot.
    sudo touch ./resume-Chituboard

    info "rebooting.."
    # reboot here
    sudo reboot
    sleep 5

else 
    warn "resuming script after reboot.."
    
    # remove the temporary file that we created to check for reboot
    sudo rm -f ./resume-Chituboard
    # continue with rest of the script

    info
    info "Setting up Chituboard prerequisites"
    echo -e "dtoverlay=dwc2\ndr_mode=peripheral\nenable_uart=1" >> /boot/config.txt
    sudo sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt
    echo -n " modules-load=dwc2" >> /boot/cmdline.txt
    # setup 4 GB container file to for storing uploaded files
    info
    info "Setting up Pi-USB; this could take several minutes"
    sudo dd bs=1M if=/dev/zero of=/piusb.bin count=4096
    sudo mkdosfs /piusb.bin -F 32 -I
    # Create the mount point for the container file
    sudo mkdir /home/pi/.octoprint/uploads/resin
    echo "/piusb.bin            /home/pi/.octoprint/uploads/resin  vfat    users,uid=pi,gid=pi,umask=000   0       2 " >> /etc/fstab

    sudo mount -a

    sudo sed -i 's/exit 0//g' /etc/rc.local

    echo '/bin/sleep 5
    modprobe g_mass_storage file=/piusb.bin removable=1 ro=0 stall=0
    exit 0' >> /etc/rc.local

    sudo systemctl stop serial-getty@ttyS0
    sudo systemctl disable serial-getty@ttyS0

    info ""
    info "Setting up Sambashare; this could take a long time"
    sudo apt-get -y install samba winbind -y

    read -r -p "Enter a short description of your printer, like the model: "  model
    echo "[USB_Share]
    comment = $model
    path = /home/pi/.octoprint/uploads/resin/
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
        read -r -p "Reboot now? [Y/n] " input
    
        case $input in
            [yY][eE][sS]|[yY])
        warn "Rebooting in 5 seconds"
        sleep 5
        echo "$(sudo reboot)"
        break
        ;;
            [nN][oO]|[nN])
        break
                ;;
            *)
        warn "Invalid input..."
        esac
    done
fi
