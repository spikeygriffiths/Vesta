#!/bin/bash
if [ -f /home/pi/hubapp/rebootflag ]; then
    rm -f /home/pi/hubapp/rebootflag
    sudo /sbin/reboot
fi

