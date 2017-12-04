<?php
include "functions.php";
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 2;  URL=$url1");
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
PageHeader("Application log now");

echo "</center>";
$logHandle = fopen("/home/pi/Vesta/today.log", "r");
fseek($logHandle, -4000, SEEK_END); // Back 4000 chars from the end (assume ~50 lines of 80 chars)
$logText = fread($logHandle, 4000);
echo nl2br($logText);

echo "<br><br>";
PageFooter();
echo "</body></html>";
?>
