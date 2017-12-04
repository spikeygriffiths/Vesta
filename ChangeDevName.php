<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
$devKey=$_GET['devKey'];
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
PageHeader("Change ".$username);
ChangeName($db, $devKey, $username);
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'\">This device</button><br><br>";
PageFooter();
echo "</body></html>";

function ChangeName($db, $devKey, $username)
{
    echo "<center><form action=\"/vesta/UpdateDeviceName.php/?devKey=",$devKey,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    echo "</table>";
    echo "<br><input type=\"submit\" value=\"Update name\"></form>";
}
?>
