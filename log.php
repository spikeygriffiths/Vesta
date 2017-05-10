<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>Today's Debug Log</h1></center>";
$logName = "/home/pi/hubapp/today.log";
//echo substr(sprintf('%o', fileperms($logName)), -4);
$logHandle = fopen($logName, "r");
$logText = fread($logHandle, 100000);
echo nl2br($logText);
echo "<br><br><a href=\"/index.php\">Home</a>";
echo "</body></html>";
?>
