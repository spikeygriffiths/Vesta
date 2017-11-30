<?php
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
$devKey=$_GET['devKey'];
include "functions.php";
include "database.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
echo "<center>";
echo "<button class=\"buttonHeader\" type=\"button\" onclick=\"window.location.href='/vesta/ChangeDevName.php/?devKey=",$devKey,"'\">",$username,"</button>";
ShowDeviceInfo($db, $devKey, $username);
echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
echo "<button class=\"buttonHome\" type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowDevStatus($item, $name, $devKey, $db)
{
    $val = GetDevStatus($item, $devKey,$db);
    if ($val != null) {
        if ($item == "presence_time") { $val = ElapsedTime($val); }   # Convert timestamp to elapsed time
        echo "<tr><td>",$name,"</td><td>$val</td></tr>";
    }
}

function ShowDevItem($item, $name, $devKey, $db)
{
    $val = GetDevItem($item, $devKey,$db);
    if ($val != null) {
        echo "<tr><td>",$name,"</td><td>$val</td></tr>";
    }
}

function ShowClusters($item, $name, $devKey, $db)
{
    $clusterDict = array(
     "Basic" => "0000",
     "PowerConfig" => "0001",
     "Identify" => "0003",
     "OnOff" => "0006",
     "LevelCtrl" => "0008",
     "OTA" => "0019",
     "PollCtrl" => "0020",
     "ColourCtrl" => "0300",
     "Illuminance" => "0400",
     "Temperature" => "0402",
     "Occupancy" => "0406",
     "IAS_Zone" => "0500",
     "SimpleMetering" => "0702",
     );

    $val = GetDevItem($item, $devKey,$db);
    if ($val != null) {
        $val = str_replace("[", "", $val); # Remove square brackets from list of clusters
        $val = str_replace("]", "", $val); # Remove square brackets from list of clusters
        $val = str_replace("'", "", $val); # Remove single quotes from list of clusters
        $list = explode(', ', $val);
        $clusterNames = array();    # Empty array of names, ready to start populating with matched items in $list
        foreach ($list as $item) {  # Go through $list, replacing 'xxxx' with named cluster
            $cluster = array_search($item, $clusterDict);
            if ($cluster === FALSE) $cluster = $item;  # If we didn't find a match, just show original item
            $clusterNames[] = $cluster; # Append each item in turn
        }
        $finalList = implode(", ", $clusterNames);
        if ($finalList == "") $finalList = "<empty>";
        echo "<tr><td>",$name,"</td><td>$finalList</td></tr>";
    }
}

function ShowEvent($devKey, $db)
{
    $result = $db->query("SELECT event FROM Events WHERE devKey=".$devKey." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[event];
    if ($val != "") echo "<td>",$val,"</td>"; else echo "<td>N/A</td>";
}

function ShowDeviceInfo($db, $devKey, $username)
{
    $nwkId = GetDevItem("nwkId", $devkey, $db);
    if ("0000" != $nwkId) {
        echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/DelDevice.php/?devId=",$username,"'\">Remove Device</button><br><br>";
    }
    //echo "<center><form action=\"/vesta/UpdateDeviceName.php/?devKey=",$devKey,"\" method=\"post\">";
    echo "<table>";
    //echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    ShowDevStatus("signal", "Radio Signal %", $devKey, $db);
    ShowDevStatus("battery", "Battery %", $devKey, $db);
    ShowDevStatus("temperature", "Temperature 'C", $devKey, $db);
    ShowDevStatus("powerReadingW", "Power (W)", $devKey, $db);
    ShowDevStatus("presence", "Presence", $devKey, $db);
    ShowDevStatus("presence_time", "Last heard", $devKey, $db);
    echo "<tr><td>Event</td>";
    ShowEvent($devKey, $db);
    echo "</tr>";
    ShowDevItem("manufName", "Manufacturer", $devKey, $db);
    ShowDevItem("modelName", "Model", $devKey, $db);
    ShowDevItem("eui64", "EUI", $devKey, $db);
    ShowDevItem("nwkId", "Network Id", $devKey, $db);
    ShowDevItem("devType", "Device Type", $devKey, $db);
    ShowDevItem("endPoints", "Endpoints", $devKey, $db);
    ShowDevItem("firmwareVersion", "Firmware Version", $devKey, $db);
    if ("0000" != $nwkId) {
        ShowClusters("inClusters", "In Clusters", $devKey, $db);
        ShowClusters("outClusters", "Out Clusters", $devKey, $db);
        ShowClusters("binding", "Binding", $devKey, $db);
        #ShowDevItem("reporting", "Reporting", $devKey, $db);
        ShowDevItem("iasZoneType", "IAS Zone Type", $devKey, $db);
    } else {    // Is Vesta coordinator
        $radioStr = AppCmd("radio", True);
        $radioInfo = explode(",", $radioStr);
        echo "<tr><td>Radio Channel</td><td>",$radioInfo[0],"</td></tr>";
        echo "<tr><td>Radio Power</td><td>",$radioInfo[1],"</td></tr>";
        echo "<tr><td>PAN Id</td><td>",$radioInfo[2],"</td></tr>";
        echo "<tr><td>Extended PAN Id</td><td>",$radioInfo[3],"</td></tr>";
    }
    echo "</table><br>";
    //echo "<input type=\"submit\" value=\"Update name\"></form>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/rules.php/?item=",$username,"'\">Rules</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/activity.php/?devKey=",$devKey,"'\">Activity Log</button>&nbsp&nbsp&nbsp";
    if ("0000" != $nwkId) {
        echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=identify ",$username," 30'\">Identify for 30s</button>&nbsp&nbsp&nbsp";
        $inClusters = GetDevItem("inClusters", $devKey, $db);
        if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=toggle ",$username,"'\">Toggle</button>&nbsp&nbsp&nbsp";
        }
        if (strpos($inClusters, "0008") !== false) { // Is dimmable, eg lamp, bulb
            echo "Brightness: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=dim&map=\"><img src=\"/vesta/UpRamp.png\" width=100 height=20 alt=\"Level\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y,
        }
        if (strpos($inClusters, "0300") !== false) { // ColorCtrl cluster, eg lamp, RGB bulbs
            echo "Hue: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=hue&map=\"><img src=\"/vesta/Hue.png\" width=360 height=20 alt=\"Hue\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y, according to stackoverflow.com/questions/358387
            echo "Saturation: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=sat&map=\"><img src=\"/vesta/Sat.png\" width=100 height=20 alt=\"Saturation\" ismap=\"ismap\"></a><br><br>";
        }
    }
}
?>
