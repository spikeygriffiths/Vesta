<?php
error_reporting(E_ALL); 
include "database.php";

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$devKey=$_GET['devKey'];
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
echo "<center><h1>Change ",$username,"</h1>";
ChangeName($db, $devKey, $username);
echo "<a href=\"/vesta/ShowAllDevices.php\">All Devices</a><br><br>";
echo "<a href=\"/vesta/ShowOneDevice.php/?devKey=",$devKey,"\">Show Device</a><br><br>";
echo "<a href=\"/vesta/index.php\">Home</a>";
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
