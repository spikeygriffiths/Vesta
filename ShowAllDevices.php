<?php 
// ShowAllDevices.php
include "database.php";
include "functions.php";
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
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
    $val = GetDevStatus($item, $devKey,$db);
    if ($val != null) {
        echo "<td>$val$suffix</td>";
    } else {
        echo "<td>N/A</td>";
    }
}

function ShowEvent($devKey, $db)
{
    $result = $db->query("SELECT * FROM Events WHERE devKey=".$devKey." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch['event'];
    $time = $fetch['timestamp'];
    $time = ElapsedTime($time);
    if ($val != "") echo "<td>",$val,"<div style=\"float:right;width:35%;\">(",$time, " ago)</td>"; else echo "<td>N/A</td>";
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
            echo "<tr>";
            $username = GetDevItem("userName", $devKey, $db);
            echo "<td><a href=\"/vesta/ShowOneDevice.php/?devKey=",$devKey,"\">",$username,"</a></td>";
	        ShowDevStatus("battery", $devKey, $db, "%");
	        ShowDevStatus("signal", $devKey, $db, "%");
      	    ShowDevStatus("presence", $devKey, $db, "");
            ShowEvent($devKey, $db);
            echo "</tr>";
        }
        echo "</table>";
    } else {
        echo "<br>No devices yet...<br>";
    }
}
?>
