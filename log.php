<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>Today's Debug Log</h1></center>";
$logHandle = fopen("/home/pi/hubapp/today.log", "r");
$logText = fread($logHandle, 100000);
echo nl2br($logText);
?>
