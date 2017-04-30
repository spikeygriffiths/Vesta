<?php 
error_reporting(E_ALL); 
include "HubCmd.php";

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>Info Command</h1></center>";
echo nl2br(HubCmd("info", true));
echo "<form action=\"/Command.php/?expRsp=true\" method=\"post\">";
echo "<table>";
echo "tr><td><input type=\"text\" name=\"cmd\"></td></tr>";
echo "</table>";
echo "<input type=\"submit\" value=\"Submit\" name=\"Send Command\"></form><br>";
echo "</body>";
?>
