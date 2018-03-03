<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
$username=$_GET['username'];
$scheduleName=$_GET['type'];
$db = DatabaseInit();
PageHeader("Change ".$scheduleName);
ChangeName($db, $username, $scheduleName);
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Schedules.php/?devKey=",$devKey,"&scheduleName'\">Schedules</button><br><br>";
PageFooter();
echo "</body></html>";

function ChangeName($db, $username, $scheduleName)
{
    echo "<center><form action=\"/vesta/UpdateScheduleName.php/?username=",$username,"&oldSchedName=",$scheduleName,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"newSchedName\" value=\"", $scheduleName, "\"></td>"; // Default new name is old one
    echo "</table>";
    echo "<br><input type=\"submit\" value=\"Update name\"></form>";
}
?>
