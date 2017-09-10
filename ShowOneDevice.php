<?php
session_start();
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
error_reporting(E_ALL); 
include "AppCmd.php";
include "database.php";

$refreshInterval = 5;   // Should probably be 10
//$url1 = $_SERVER['PHP_SELF']; // Seems to lose args on URL line when refreshing?
//header("Refresh: $refreshInterval;  URL=$url1");
echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "<meta http-equiv=\"refresh\" content=\"",$refreshInterval,"\">";    // Auto-refresh page.  NB Must be inside <head>
echo "</head>";
echo "<body>";
$devKey=$_GET['devKey'];
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
echo "<center><h1>",$username,"</h1>";
ShowDeviceInfo($db, $devKey, $username);
echo "<br><br><button type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowDevStatus($item, $name, $devKey, $db)
{
    $val = GetDevStatus($item, $devKey,$db);
    if ($val != null) {
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
        echo "<button type=\"button\" onclick=\"window.location.href='/vesta/DelDevice.php/?devId=",$username,"'\">Remove Device</button><br><br>";
    }
    //echo "<center><form action=\"/vesta/UpdateDeviceName.php/?devKey=",$devKey,"\" method=\"post\">";
    echo "<table>";
    //echo "<tr><td>Name</td><td><input type=\"text\" name=\"UserName\" value=\"", $username, "\"></td>";
    ShowDevStatus("signal", "Radio Signal %", $devKey, $db);
    ShowDevStatus("battery", "Battery %", $devKey, $db);
    ShowDevStatus("temperature", "Temperature 'C", $devKey, $db);
    ShowDevStatus("powerReadingW", "Power (W)", $devKey, $db);
    ShowDevStatus("presence", "Presence", $devKey, $db);
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
        ShowDevItem("inClusters", "In Clusters", $devKey, $db);
        ShowDevItem("outClusters", "Out Clusters", $devKey, $db);
        ShowDevItem("binding", "Binding", $devKey, $db);
        ShowDevItem("reporting", "Reporting", $devKey, $db);
        ShowDevItem("iasZoneType", "IAS Zone Type", $devKey, $db);
    } else {    // Is Vesta coordinator
        $radioStr = AppCmd("radio", True);
        $radioInfo = explode(",", $radioStr);
        echo "<tr><td>Radio Channel</td><td>",$radioInfo[0],"</td></tr>";
        echo "<tr><td>Radio Power</td><td>",$radioInfo[1],"</td></tr>";
        echo "<tr><td>PAN Id</td><td>",$radioInfo[2],"</td></tr>";
        echo "<tr><td>Extended PAN Id</td><td>",$radioInfo[3],"</td></tr>";
    }
    echo "</table>";
    //echo "<input type=\"submit\" value=\"Update name\"></form>";
    echo "<br><button type=\"button\" onclick=\"window.location.href='/vesta/ChangeDevName.php/?devKey=",$devKey,"'\">Change Name</button>&nbsp&nbsp&nbsp";
    echo "<button type=\"button\" onclick=\"window.location.href='/vesta/rules.php/?item=",$username,"'\">Rules</button>&nbsp&nbsp&nbsp";
    echo "<button type=\"button\" onclick=\"window.location.href='/vesta/activity.php/?devKey=",$devKey,"'\">Activity Log</button>&nbsp&nbsp&nbsp";
    if ("0000" != $nwkId) {
        echo "<button type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=identify ",$username," 30'\">Identify for 30s</button>&nbsp&nbsp&nbsp";
        $inClusters = GetDevItem("inClusters", $devKey, $db);
        if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
            echo "<button type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=toggle ",$username,"'\">Toggle</button>&nbsp&nbsp&nbsp";
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
