<?php
# DevConfig.php
$devKey=$_GET['devKey'];
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
echo "<center>";
$title = "Configuration for ".$username;
PageHeader($title);
ShowDeviceConfig($db, $devKey, $username);
echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'\">",$username,"</button>";
echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
PageFooter();
echo "</body></html>";

function ShowItemConfig($name, $field, $notes, $default, $devKey, $db)
{
    $reporting = GetDevItem($field, $devKey,$db);
    if (($reporting == None) || (substr_count($reporting, ",") != 2)) {
        $reporting = $default;  # Convert any illegal strings to a sensible default
    }
    $reportingList = str_getcsv($reporting);
    $min = $reportingList[0];
    $max = $reportingList[1];
    $delta = $reportingList[2];
    echo "<tr><td>",$name,"</td>";
    echo "<form action=\"/vesta/configChange.php/?devKey=", $devKey, "&field=", $field, "\" method=\"post\">";
    echo "<td><input type=\"number\" min=\"-1\" max=\"65534\" name=\"min\" value=\"", $min, "\"></td>";
    echo "<td><input type=\"number\" min=\"-1\" max=\"65534\" name=\"max\" value=\"", $max, "\"></td>";
    echo "<td><input type=\"number\" min=\"0\" name=\"delta\" value=\"", $delta, "\"></td>";
    echo "<td><input type=\"submit\" value=\"Update\"></td>";
    echo "<td>",$notes,"</td>";
    echo "</form>";
    echo "</tr>";
}

function ShowDeviceConfig($db, $devKey, $username)
{
   $val = GetDevItem("inClusters", $devKey,$db);
    if ($val != null) {
        echo "(Disable report by using -1 as Max time)<br><br>";
        echo "<table>";
        echo "<tr><th>Reportable item</th><th>Min (Secs)</th><th>Max (Secs)</th><th>Delta</th><th>Update</th><th>Notes</th></tr>";
        if (strpos($val, "0001") !== false) {   # Found PowerConfig
            ShowItemConfig("Battery", "batteryReporting", "in 0.5% units", "43200,43200,2", $devKey, $db);
        }
        if (strpos($val, "0402") !== false) {   # Found Temperature
            ShowItemConfig("Temperature", "temperatureReporting", "in 0.01'C units", "300,3600,100", $devKey, $db);
        }
        if (strpos($val, "0702") !== false) {   # Found SimpleMetering - need three items here
            ShowItemConfig("Power", "powerReporting", "in Watts", "-1,-1,10", $devKey, $db);
            ShowItemConfig("EnergyConsumed", "energyConsumedReporting", "in WattHours", "-1,-1,100", $devKey, $db);
            ShowItemConfig("EnergyGenerated", "energyGeneratedReporting", "in WattHours", "-1,-1,100", $devKey,$db);
        }
        echo "</table>";
        if (strpos($val, "0020") != false) {   # Found PollCtrl
            # Only has frequency of checkins, so is different to other reporting
        }
        if (strpos($val, "0406") != false) {   # Found Occupancy
            # Has PIR sensitivity, so is different to other reporting
        }
    }
}
?>
