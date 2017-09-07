<?php
$fh = fopen("/home/pi/Vesta/rebootflag", 'w');
fwrite($fh, "reboot now");  // Could write anything here - checkreboot.sh just checks for existence of file
fclose($fh);
echo "<html>";
echo "<body>";
echo "Restarting linux within the next minute or two.  ";
echo "</body></html>";
?>
