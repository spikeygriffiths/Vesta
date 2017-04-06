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
echo "<center><h1>",$username,"</h1>";
ShowDeviceInfo($db, $devIdx, $username);
echo "<a href=\"/ShowAllDevices.php\">All Devices</a><br><br>";
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

function ShowEvent($devIdx, $db)
{
    $result = $db->query("SELECT event FROM Events WHERE devIdx=".$devIdx." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[event];
    if ($val != "") echo "<td>",$val,"</td>"; else echo "<td>N/A</td>";
}

function ShowDeviceInfo($db, $devIdx, $username)
{
    echo "<center><form action=\"/UpdateDeviceName.php/?devIdx=",$devIdx,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    ShowDevStatus("signal", "Radio Signal %", $devIdx, $db);
    ShowDevStatus("battery", "Battery %", $devIdx, $db);
    ShowDevStatus("temperature", "Temperature 'C", $devIdx, $db);
    ShowDevItem("powerReading", "Power (W)", $devIdx, $db);
    ShowDevStatus("presence", "Presence", $devIdx, $db);
    echo "<tr><td>Event</td>";
    ShowEvent($devIdx, $db);
    echo "</tr>";
    ShowDevItem("manufName", "Manufacturer", $devIdx, $db);
    ShowDevItem("modelName", "Model", $devIdx, $db);
    ShowDevItem("eui64", "EUI", $devIdx, $db);
    ShowDevItem("nwkId", "Network Id", $devIdx, $db);
    ShowDevItem("devType", "Device Type", $devIdx, $db);
    ShowDevItem("endPoints", "Endpoints", $devIdx, $db);
    if ($devIdx != 0) {
        ShowDevItem("inClusters", "In Clusters", $devIdx, $db);
        ShowDevItem("outClusters", "Out Clusters", $devIdx, $db);
        ShowDevItem("binding", "Binding", $devIdx, $db);
        ShowDevItem("reporting", "Reporting", $devIdx, $db);
        ShowDevItem("iasZoneType", "IAS Zone Type", $devIdx, $db);
    } else {    // Is hub
        $radioStr = HubCmd("radio", True);
        $radioInfo = explode(",", $radioStr);
        echo "<tr><td>Radio Channel</td><td>",$radioInfo[0],"</td></tr>";
        echo "<tr><td>Radio Power</td><td>",$radioInfo[1],"</td></tr>";
        echo "<tr><td>PAN Id</td><td>",$radioInfo[2],"</td></tr>";
        echo "<tr><td>Extended PAN Id</td><td>",$radioInfo[3],"</td></tr>";
    }
    echo "</table>";
    echo "<input type=\"submit\" value=\"Update name\"></form>";
    echo "<A href=\"/Command.php/?cmd=identify ",$username," 30\">Identify for 30s</A><br><br>";
    $inClusters = DevGetItem("inClusters", $devIdx, $db);
    if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
        echo "<A href=\"/Command.php/?cmd=toggle ",$username,"\">Toggle</A><br><br>";
    }
    if (strpos($inClusters, "0008") !== false) { // Is dimmable, eg lamp, bulb
        echo "Brightness: <a href=\"/ImageMap.php/?devId=",$username,"&cmd=dim&map=\"><img src=\"/UpRamp.png\" width=100 height=20 alt=\"Level\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y,
    }
    if (strpos($inClusters, "0300") !== false) { // ColorCtrl cluster, eg lamp, RGB bulbs
        echo "Hue: <a href=\"/ImageMap.php/?devId=",$username,"&cmd=hue&map=\"><img src=\"/Hue.png\" width=360 height=20 alt=\"Hue\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y, according to stackoverflow.com/questions/358387
        echo "Saturation: <a href=\"/ImageMap.php/?devId=",$username,"&cmd=sat&map=\"><img src=\"/Sat.png\" width=100 height=20 alt=\"Saturation\" ismap=\"ismap\"></a><br><br>";
    }
}
?>
