<?php 
include "database.php";
include "functions.php";
include "AppCmd.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
PageHeader("Info Command");
echo nl2br(AppCmd("info", true));
//echo "<form action=\"/vesta/Command.php/?expRsp=true\" method=\"post\">";
//echo "<table>";
//echo "tr><td><input type=\"text\" name=\"cmd\"></td></tr>";
//echo "</table>";
//echo "<input type=\"submit\" value=\"Submit\" name=\"Send Command\"></form><br>";
PageFooter();
echo "</body></html>";
?>
