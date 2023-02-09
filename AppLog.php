<?php
include "database.php";
include "functions.php";
$url1 = $_SERVER['REQUEST_URI'];
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<meta http-equiv=\"refresh\" content=\"2\">";
echo "</head><body>";
PageHeader("Application log now");

echo "</center>";
$logHandle = fopen("/home/pi/Vesta/logs/today.log", "r");
fseek($logHandle, -10000, SEEK_END); // Back 10000 chars from the end
$logText = fread($logHandle, 10000);
echo nl2br($logText);

echo "<br><br>";
PageFooter();
echo "</body></html>";
?>
