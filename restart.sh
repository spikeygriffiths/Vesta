if ps ax | grep -v grep | grep vesta.py ; then
    echo "Vesta running"
else
    (cd /home/pi/hubapp; [ -e err.log ] && mv err.log olderr.log ; ./vesta.py 2> err.log) &
    echo "Vesta restarting..."
fi

