<?php 
// ShowAllDevices.php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<meta http-equiv=\"refresh\" content=\"10\">";
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</head><body>";
$rightBtn = "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/AddNewDevices.php'\">Add</button>";
PageHeader("All Devices", $rightBtn);
//print_r (PDO::getAvailableDrivers()); echo("<br>"); // Shows whether SQLite for PDO is installed
ShowDevices();
echo "<br>";
PageFooter();
echo "</body></html>";

function ShowDevStatus($item, $devKey, $db, $suffix)
{
    $row = GetLatestLoggedItem($item, $devKey,$db);
    if ($row != null) {
        $val = $row['value'];
        echo "<td>$val$suffix</td>";
    } else {
        echo "<td>N/A</td>";
    }
}

function ShowState($devKey, $db)
{
    $row = GetLatestLoggedItem("State", $devKey,$db);
    if ($row != null) {
        $val = $row['value'];
        $time = $row['timestamp'];
        $time = ElapsedTime($time);
        if ($val != "") echo "<td>",$val,"<div style=\"float:right;width:35%;\">(",$time, " ago)</td>"; else echo "<td>N/A</td>";
    } else echo "<td>N/A</td>";
}

function ShowDevices()
{
    $db = DatabaseInit();
    $numDevs = GetDevCount($db);
    if ($numDevs > 0) {
        echo "<table>";
        echo "<tr><th>Name</th><th>Battery</th><th>Signal</th><th>Presence</th><th width=\"400\">Notes</th></tr>";
        for ($index = 0; $index < $numDevs; $index++) {
            $devKey = GetDevKey($index, $db);
            $devKeys[] = $devKey;
            $usernames[] = GetDevItem("userName", $devKey, $db);
        }
        array_multisort($usernames, SORT_ASC, SORT_NATURAL | SORT_FLAG_CASE, $devKeys);  # Sort usernames and make sure devKeys follows suit
        for ($index = 0; $index < sizeof($devKeys); $index++) {
            $devKey = $devKeys[$index];
            $username = $usernames[$index];
            echo "<tr>";
            echo "<td><a href=\"/vesta/ShowOneDevice.php/?devKey=",$devKey,"\">",$username,"</a></td>";
	        ShowDevStatus("BatteryPercentage", $devKey, $db, "%");
	        ShowDevStatus("SignalPercentage", $devKey, $db, "%");
      	    ShowDevStatus("Presence", $devKey, $db, "");
            ShowState($devKey, $db);
            echo "</tr>";
        }
        echo "</table>";
    } else {
        echo "<br>No devices yet...<br>";
    }
}
?>
