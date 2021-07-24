# Octoprint-Chituboard
Added basic support chituboard based printers(Elegoo Mars, Anycubic Photon, Phrozen, etc.) to octoprint.
* upload files to folder `~/.octoprint/uploads/resin`
* pause and resume are still somewhat buggy
* File analysis CLI command works `octoprint plugins Chituboard:sla_analysis NAME`
* Todo: finish Analysis factory after I figure out how to use sarge 
* Todo: fix hacky mess written to handle actions after print finished
* Todo: write model viewer to display layer slices and relevant info
    Anyone is welcome to take this on, I'm terrible at javascript

## Hardware setup
Hardware setup instructions

### Requirements
1. **Raspberry Pi Zero W, Zero WH, 3A+ or 4B** only supports raspberry pi's with USB-OTG ports
2. Supported printers: SLA printers with chitu3d mainboard
  * Anycubic Photon
  * Elegoo Mars
  * Elegoo Mars Pro
  * Elegoo Mars 2
  * Elegoo Mars 2 Pro
  * Elegoo Saturn
  * Phrozen Sonic Mighty 4K
  * Phrozen Sonic Mini 4K
  * Creality LD-002H
  * Creality LD-002R
  * Voxelab Proxima
  * Peopoly Phenom L
  * EPAX E10/X10

### Connecting Pi to printers USB port

Our goal here is to use the Pi as a USB flash drive. The printer mainboards use the USB port to read USB FAT storage devices not for serial control. The printer can only supply around 500 mA via the 5V line so its best to power you pi with an external power source.
Follow one of these steps.
1. Put some tape on the 5V line of your USB cable. This [tutorial](https://l9o.dev/posts/controlling-an-elegoo-mars-pro-remotely/) is a good reference on how to do this.
2. Cut the connection between the 5V line and the USB port on the Pi. Some people online do this, but I didn’t want to do any permanent changes to my Pi.
3. The USB-OTG port on the Raspberry pi 4B is also the USB host port
  * users should put tape on the USB-A end of your USB C to USB A cable
  * users will also need to power the pi via the GPIO pins, I suggest using the [X735](https://wiki.geekworm.com/X735).
  * users who forget to tape over the 5V pin on will risk frying their pi 4B

### Connecting the Pi to the printer’s serial port

Follow tutorial from [Mariner blog post](https://l9o.dev/posts/controlling-an-elegoo-mars-pro-remotely/) for more detailed hardware setup process.

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

