<?php 
include "database.php";
include "AppCmd.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
echo "<center><h1>Info Command</h1></center>";
echo nl2br(AppCmd("info", true));
//echo "<form action=\"/vesta/Command.php/?expRsp=true\" method=\"post\">";
//echo "<table>";
//echo "tr><td><input type=\"text\" name=\"cmd\"></td></tr>";
//echo "</table>";
//echo "<input type=\"submit\" value=\"Submit\" name=\"Send Command\"></form><br>";
echo "<br><br><a href=\"/vesta/index.php\">Home</a>";
echo "</body></html>";
?>
