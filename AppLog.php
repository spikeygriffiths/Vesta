<?php
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 2;  URL=$url1");
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
echo "<center><h1>Application log now</h1></center>";

$logHandle = fopen("/home/pi/Vesta/today.log", "r");
fseek($logHandle, -2000, SEEK_END); // Back 2000 chars from the end (assume ~25 lines of 80 chars)
$logText = fread($logHandle, 2000);
echo nl2br($logText);

echo "<br><br>";
echo "<button class=\"buttonHome\" type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";
?>
