# Octoprint-Chituboard
Added basic support chituboard based printers(Elegoo Mars, Anycubic Photon, Phrozen, etc.) to octoprint.


## Raspberry pi flash drive setup
This script is intended for a fresh octopi installation on a Raspberry Pi Zero or raspberry pi 4

It will set up a folder on the Pi as a USB drive using the USB-OTG, create a sambashare, and a couple other things.

### Download
Either from this Github or using
`wget https://raw.githubusercontent.com/rudetrooper/Octoprint-Chituboard/main/Chituboard.sh`

### Prepare for execution
`sudo chmod +x ./Chituboard.sh`

### Execute
`sudo bash ./Chituboard.sh`

Follow the prompts in the script, reboot, and run once more.
You should see a different set of prompts on the second run

