<?php
error_reporting(E_ALL); 
include "HubCmd.php";

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$devIdx=$_GET['devIdx'];
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$username = DevGetItem("userName", $devIdx,$db);
echo "<center><h1>Change ",$username,"</h1>";
ChangeName($db, $devIdx, $username);
echo "<a href=/ShowOneDevice.php/?devIdx=",$devIdx,">Show Device</a>";
echo "<a href=\"/index.php\">Home</a>";
echo "</body></html>";

function  DevGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function ChangeName($db, $devIdx, $username)
{
    echo "<center><form action=\"/UpdateDeviceName.php/?devIdx=",$devIdx,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    echo "</table>";
    echo "<input type=\"submit\" value=\"Update name\"></form>";
}
?>
