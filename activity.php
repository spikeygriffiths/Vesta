<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$db = DatabaseInit();
$dbTime = $_GET['dbTime'];
$titleTime = $_GET['titleTime'];
if (empty($titleTime) || empty($dbTime)) {
    $dbTime = "date('now', 'start of day')";
    $titleTime = "Today";
}
$devKey = $_GET['devKey'];
if ($devKey==-1) {
    $title = "All activity from ".$titleTime;
} else {
    $userName = GetDevItem("userName", $devKey, $db);
    $title = "Activity for ".$userName." from ".$titleTime;
}
PageHeader($title);
// See if the time needs to be adjusted
echo "<form action='/vesta/SelectActivityTime.php/?devKey=".$devKey."' method='post'>";
echo "<p>Show events from:<select id='timePeriod' name='timePeriod'>";
echo "<option value='today'>Today</option>";
echo "<option value='yesterday'>Yesterday onwards</option>";
echo "<option value='week'>Last week</option>";
echo "<option value='month'>Last 30 days</option>";
echo "</select>";
echo "<input type='submit' name='submit'/>";
echo "</form>";
ShowActivity($db, $dbTime, $titleTime, $devKey);
echo "<br>";
PageFooter();
echo "</body></html>";

function ShowActivity($db, $dbTime, $titleTime, $devKey)
{
    if ($devKey==-1) {
        //echo "<h3>Showing all activity from ",$titleTime,"</h3>";
        $sth = $db->prepare("SELECT * FROM Events WHERE timestamp > ".$dbTime);
    } else {
        //$userName = GetDevItem("userName", $devKey, $db);
        //echo "<h3>Showing activity for ",$userName," from ",$titleTime,"</h3>";
        $sth = $db->prepare("SELECT * FROM Events WHERE devKey=".$devKey." AND timestamp > ".$dbTime);
    }
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $userName = GetDevItem("userName", $row['devKey'],$db);        // Use $row['devKey'] as key into Devices table to get $userName
        echo"<tr><td> ".$row['timestamp']." </td><td>".$userName." </td><td> ".$row['event']." </td></tr>";
    }
    echo "</table>";
}

?>
