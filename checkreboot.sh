#!/bin/bash
if [ -f /home/pi/Vesta/rebootflag ]; then
    rm -f /home/pi/Vesta/rebootflag
    sudo /sbin/reboot
fi

