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
$username = DevGetItem("userName", $devIdx,$db);
echo "<center><h1>",$username,"</h1></center>";
ShowDeviceInfo($db, $devIdx, $username);
echo "<center><a href=\"/ShowAllDevices.php\">All Devices</a> </center><br>";
echo "<center><a href=\"/index.php\">Home</a> </center>";
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

function  DevGetStatus($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Status WHERE devIdx=".$devIdx);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function ShowDevStatus($item, $name, $devIdx, $db)
{
    $val = DevGetStatus($item, $devIdx,$db);
    if ($val != null) {
        echo "<tr><td>",$name,"</td><td>$val</td></tr>";
    }
}

function ShowDevItem($item, $name, $devIdx, $db)
{
    $val = DevGetItem($item, $devIdx,$db);
    if ($val != null) {
        echo "<tr><td>",$name,"</td><td>$val</td></tr>";
    }
}

function ShowLatest($item, $devIdx, $db)
{
    $result = $db->query("SELECT value FROM Events WHERE item=\"".$item."\" AND devIdx=".$devIdx." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    if ($fetch) {
        $val = $fetch[value];
        if ($val) {
            echo "<tr><td>",$item,"</td><td>$val</td></tr>";
        }
    }
}

function ShowDeviceInfo($db, $devIdx, $username)
{
    echo "<form action=\"/UpdateDeviceName.php/?devIdx=",$devIdx,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    ShowDevStatus("signal", "Radio Signal %", $devIdx, $db);
    ShowDevStatus("battery", "Battery %", $devIdx, $db);
    ShowDevStatus("temperature", "Temperature 'C", $devIdx, $db);
    ShowDevStatus("presence", "Presence", $devIdx, $db);
    ShowLatest("Event", $devIdx, $db);
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
    echo "</table>";
    echo "<input type=\"submit\" value=\"Submit\" name=\"Update name\"></form><br>";
    $inClusters = DevGetItem("inClusters", $devIdx, $db);
    if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
        echo "<A href=\"/Command.php/?cmd=toggle ",$username,"\">Toggle</A><br>";
    }
}

?>
