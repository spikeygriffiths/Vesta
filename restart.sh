if ps ax | grep -v grep | grep vesta.py ; then
    echo "Vesta running"
else
    (cd /home/pi/hubapp; ./vesta.py) &
    echo "Vesta restarting..."
fi

