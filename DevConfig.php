<?php
# DevConfig.php
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
$title = "Configuration for ".$username;
PageHeader($title);
ShowDeviceConfig($db, $devKey, $username);
echo "<br><br><button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
PageFooter();
echo "</body></html>";


function ShowDeviceConfig($db, $devKey, $username)
    $val = GetDevItem("inClusters", $devKey,$db);
    if ($val != null) {
        echo "<table>";
        echo "<tr><th>Reportable item</th><th>Min (Secs)</th><th>Max (Secs)</th><th>Delta</th><th>Enabled</th></tr>";
        if (strpos($val, "0001") != false) {   # Found PowerConfig
            $battReporting[] = str_getcsv(GetDevItem("batteryReporting", $devKey,$db));
            $enabled = $battReporting[0];
            $min = $battReporting[1];
            $max = $battReporting[2];
            $delta = $battReporting[3];
            echo "<tr><td>Battery</td>";
            echo "<td><input type=\"text\" name=\"battEnabled\" value=\"", $enabled, "\"></td>";
            echo "<td><input type=\"text\" name=\"battMinS\" value=\"", $min, "\"></td>";
            echo "<td><input type=\"text\" name=\"battMaxS\" value=\"", $max, "\"></td>";
            echo "<td><input type=\"text\" name=\"battDelta\" value=\"", $delta, "\"></td>";
            echo "</tr>";
        }
        if (strpos($val, "0402") != false) {   # Found Temperature
        }
        if (strpos($val, "0702") != false) {   # Found SimpleMetering - need three items here
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
