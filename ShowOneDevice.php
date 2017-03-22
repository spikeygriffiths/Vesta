<?php
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$devIdx=$_GET['devIdx'];
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$username = DbGetItem("userName", $devIdx,$db);
echo "<center><h1>",$username,"</h1></center>";
ShowDeviceInfo($db, $devIdx, $username);
echo "<center><a href=\"/ShowAllDevices.php\">All Devices</a> </center><br>";
echo "<center><a href=\"/index.php\">Home</a> </center>";
echo "</body></html>";

function  DbGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowDevItem($item, $name, $devIdx, $db)
{
    $val = DbGetItem($item, $devIdx,$db);
    echo "<tr><td>",$name,"</td><td>";
    if ($val != "") echo $val; else echo "N/A,";
    echo "</td></tr>";
}

function ShowLatest($item, $units, $devIdx, $db)
{
    $result = $db->query("SELECT value FROM Events WHERE item=\"".$item."\" AND devIdx=".$devIdx." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[value];
    echo "<tr><td>",$item,"</td><td>";
    if ($val != "") echo $val,$units; else echo "N/A";
    echo "</td></tr>";
}

function ShowDeviceInfo($db, $devIdx, $username)
{
    echo "<form action=\"/UpdateDeviceName.php/?devIdx=",$devIdx,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    ShowLatest("Battery", "%", $devIdx, $db);
    ShowLatest("Temperature", "'C", $devIdx, $db);
    ShowLatest("Presence", "", $devIdx, $db);
    ShowLatest("Event", "", $devIdx, $db);
    ShowDevItem("manufName", "Manufacturer", $devIdx, $db);
    ShowDevItem("modelName", "Model", $devIdx, $db);
    ShowDevItem("eui64", "EUI", $devIdx, $db);
    ShowDevItem("nwkId", "Network Id", $devIdx, $db);
    ShowDevItem("devType", "Device Type", $devIdx, $db);
    ShowDevItem("endPoints", "Endpoints", $devIdx, $db);
    ShowDevItem("inClusters", "In Clusters", $devIdx, $db);
    ShowDevItem("outClusters", "Out Clusters", $devIdx, $db);
    ShowDevItem("binding", "Binding", $devIdx, $db);
    ShowDevItem("reporting", "Reporting", $devIdx, $db);
    ShowDevItem("iasZoneType", "IAS Zone Type", $devIdx, $db);
    $inClusters = DbGetItem("inClusters", $devIdx, $db);
    echo "</table>";
    echo "<input type=\"submit\" value=\"Submit\" name=\"Update name\"></form><br>";
    if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
        echo "<A href=\"/Command.php/?cmd=toggle ",$username,"\">Toggle</A><br>";
    }
}
?>
