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
if (0 != $devKey) {
    $rightBtn = "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/DelDevice.php/?devId=".$username."'\">Remove</button>";
    PageHeader($username, $rightBtn);
} else {
    PageHeader($username);
}
ShowDeviceInfo($db, $devKey, $username);
echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
PageFooter();
echo "</body></html>";

function ShowDevStatus($item, $name, $units, $minAge, $devKey, $db)
{
    $row = GetLatestLoggedItem($item, $devKey,$db);
    if ($row != null) {
        $val = $row['value'];
        $time = $row['timestamp'];
        $age = ElapsedSecs($time);  # Get age in seconds
        $ageStr = ElapsedTime($time);   # Convert timestamp to elapsed time as a string
        if ($age > $minAge) { # Check how recent reading is and show age if old enough
            echo "<tr><td>",$name,"</td><td>",$val,$units,"<div style=\"float:right;width:50%;\">(",$ageStr, " ago)</div></td></tr>";
        } else {    # Don't show age of reading
            echo "<tr><td>",$name,"</td><td>",$val,$units,"</td></tr>";
        }
    }
}

function ShowDevEnergy($item, $name, $units, $devKey, $db)
{
    $row = GetLatestLoggedItem($item, $devKey,$db); # Get energy now
    if ($row != null) {
        $nowVal = $row['value'];
        $dbTime = "date('now', 'start of day')";
        $row = GetTimedLoggedItem($item, $devKey,$dbTime,$db);    # Get first Energy today
        if ($row != null) {
            $startVal = $row['value'];
            $dbTime = $row['timestamp'];    # Get actual time of first energy report
            $val = $nowVal - $startVal; # Energy used so far today
            $time = ElapsedTime($dbTime);   # Convert timestamp to elapsed time
            echo "<tr><td>",$name,"</td><td>",$val,$units,"<div style=\"float:right;width:50%;\">(Since midnight)</div></td></tr>";
            #echo "<tr><td>",$name,"</td><td>",$val,$units,"<div style=\"float:right;width:50%;\">(last ",$time,")</div></td></tr>";
        }
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
     "Groups" => "0004",
     "Scenes" => "0005",
     "OnOff" => "0006",
     "LevelCtrl" => "0008",
     "Alarms" => "0009",
     "Time" => "000A",
     "OTA" => "0019",
     "PollCtrl" => "0020",
     "Thermostat" => "0201",
     "ThermostatUI" => "0204",
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
    $result = $db->query("SELECT * FROM Events WHERE devKey=".$devKey." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $event = $fetch['event'];
    $time = $fetch['timestamp'];
    $reason = $fetch['reason'];
    $time = ElapsedTime($time);
    if ($event != "") {
        echo "<tr><td>Event</td><td>";
        if ($reason) {
            echo "<a href=\"/vesta/ShowReason.php/?event=",$event,"&reason=",$reason,"\">",$event,"</a>";
        } else {
            echo $event;    // No reason given
        }
        echo "<div style=\"float:right;width:50%;\">(",$time, " ago)</div></td>";
        echo "</tr>";
    }
}

function ShowDeviceInfo($db, $devKey, $username)
{
    $nwkId = GetDevItem("nwkId", $devkey, $db);
    echo "<table>";
    ShowDevStatus("Presence", "Presence", "", 300, $devKey, $db);
    ShowDevStatus("State", "State", "", 300, $devKey, $db);
    ShowDevStatus("SignalPercentage", "Radio Signal", "%", 300, $devKey, $db);
    ShowDevStatus("BatteryPercentage", "Battery", "%", 0, $devKey, $db);
    ShowDevStatus("TemperatureCelsius", "Temperature", "'C", 600, $devKey, $db);
    ShowDevStatus("SourceCelsius", "Source Temperature", "'C", 900, $devKey, $db);
    ShowDevStatus("TargetCelsius", "Target Temperature", "'C", 900, $devKey, $db);
    ShowDevStatus("PowerReadingW", "Power", "W", 60, $devKey, $db);
    ShowDevEnergy("EnergyConsumedWh", "Energy consumed", "Wh", $devKey, $db);
    ShowDevEnergy("EnergyGeneratedWh", "Energy generated", "Wh", $devKey, $db);
    ShowDevStatus("Time", "Time", "", 60, $devKey, $db);
    ShowEvent($devKey, $db);
    ShowDevItem("manufName", "Manufacturer", $devKey, $db);
    ShowDevItem("modelName", "Model", $devKey, $db);
    ShowDevItem("eui64", "EUI", $devKey, $db);
    ShowDevItem("nwkId", "Network Id", $devKey, $db);
    ShowDevItem("devType", "Device Type", $devKey, $db);
    ShowDevItem("endPoints", "Endpoints", $devKey, $db);
    ShowDevItem("firmwareVersion", "Firmware Version", $devKey, $db);
    if ($devKey != 0) { # 0 is always Vesta co-ordinator, so don't show clusters and binding for that
        ShowClusters("inClusters", "In Clusters", $devKey, $db);
        ShowClusters("outClusters", "Out Clusters", $devKey, $db);
        ShowClusters("binding", "Binding", $devKey, $db);
        #ShowDevItem("reporting", "Reporting", $devKey, $db);
        ShowDevItem("iasZoneType", "IAS Zone Type", $devKey, $db);
        ShowDevItem("longPollInterval", "Long Poll Interval (S)", $devKey, $db);
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
    if ("0000" != $nwkId) {    // Only show Config button if not Vesta
        $inClusters = GetDevItem("inClusters", $devKey, $db);
        if (strpos($inClusters, "0001") || strpos($inClusters, "0402") || strpos($inClusters, "0702")) { // Check if we have suitable clusters
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/DevConfig.php/?devKey=",$devKey,"'\">Configure device</button>&nbsp&nbsp&nbsp";
        }
    }
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ChangeDevName.php/?devKey=".$devKey."'\">Change Name</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/rules.php/?item=",$username,"&type=dev&devKey=",$devKey,"'\">Rules</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/activity.php/?devKey=",$devKey,"'\">Activity Log</button>&nbsp&nbsp&nbsp";
    if ("0000" != $nwkId) {
        echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=identify ",$username," 30'\">Identify for 30s</button><br><br>";
        $inClusters = GetDevItem("inClusters", $devKey, $db);
        if (strpos($inClusters, "0006") !== false) { // Is switchable, eg smartplug, bulb, etc.
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=toggle ",$username,"'\">Toggle</button>&nbsp&nbsp&nbsp";
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=on ",$username,"'\">On</button>&nbsp&nbsp&nbsp";
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=off ",$username,"'\">Off</button>&nbsp&nbsp&nbsp";
        }
        if (strpos($inClusters, "0008") !== false) { // Is dimmable, eg lamp, bulb
            echo "Brightness: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=dim&map=\"><img src=\"/vesta/UpRamp.png\" width=100 height=20 alt=\"Level\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y,
        }
        if (strpos($inClusters, "0300") !== false) { // ColorCtrl cluster, eg lamp, RGB bulbs
            echo "Hue: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=hue&map=\"><img src=\"/vesta/Hue.png\" width=360 height=20 alt=\"Hue\" ismap=\"ismap\"></a><br><br>";  // Php page will GET x,y, according to stackoverflow.com/questions/358387
            echo "Saturation: <a href=\"/vesta/ImageMap.php/?devId=",$username,"&cmd=sat&map=\"><img src=\"/vesta/Sat.png\" width=100 height=20 alt=\"Saturation\" ismap=\"ismap\"></a><br><br>";
        }
        if (strpos($inClusters, "0201") !== false) { // Thermostat cluster
            $type = GetConfig("HeatingSchedule", "Heating", $db);
            $boostDegC = GetConfig("BoostDegC", "18", $db);
            $frostDegC = GetConfig("FrostDegC", "7", $db);
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Schedule.php/?type=",$type,"&devKey=",$devKey,"'\">Schedule</button>&nbsp&nbsp&nbsp";
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setTargetTemp ",$username," ",$boostDegC," 3600'\">Boost</button>&nbsp&nbsp&nbsp"; 
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setTargetTemp ",$username," ",$frostDegC," 3600'\">Frost</button><br><br>";
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setTargetTemp ",$username," 15 60'\">Test 15C 1min</button><br><br>";
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=getTargetTemp ",$username,"'\">GetTargetTemp</button>&nbsp&nbsp&nbsp"; 
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=rptTemp ",$username," 12.34'\">SetSourceTemp as 12.34C</button>&nbsp&nbsp&nbsp"; 
            AppCmd("getSourceTemp ".$username, false);
            //AppCmd("getTargetTemp ".$username, false);  # Automatically ask for these 
        }
        if (strpos($inClusters, "000A") !== false) { // Time cluster
            echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=getTime ",$username,"'\">Get time</button>&nbsp&nbsp&nbsp";
            #AppCmd("getTime ".$username, false);
        }
    }
}
?>

