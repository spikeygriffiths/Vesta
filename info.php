<?php 
session_start();
error_reporting(E_ALL); 
include "database.php";
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
include "AppCmd.php";

echo "<html><head>";
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
