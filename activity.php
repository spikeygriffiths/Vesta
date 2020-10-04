<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$db = DatabaseInit();
if (isset($_GET['dbTime']))
    $dbTime = $_GET['dbTime'];
else
    $dbTime = "date('now', 'start of day')";
if (isset($_GET['titleTime']))
    $titleTime = $_GET['titleTime'];
else
    $titleTime = "Today";
if (isset($_GET['devKey']))
    $devKey = $_GET['devKey'];
else
    $devkey = -1;
if ($devKey == -1) {
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
if ($devKey!=-1) {
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'\">",$userName,"</button><br><br>";
}
PageFooter();
echo "</body></html>";

function ShowActivity($db, $dbTime, $titleTime, $devKey)
{
    if ($devKey==-1) {
        $sth = $db->prepare("SELECT * FROM Events WHERE timestamp > ".$dbTime);
    } else {
        $sth = $db->prepare("SELECT * FROM Events WHERE devKey=".$devKey." AND timestamp > ".$dbTime);
    }
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $userName = GetDevItem("userName", $row['devKey'],$db);        // Use $row['devKey'] as key into Devices table to get $userName
        $reason = $row['reason']; # This may refer to a rule's Rowid (if it's not empty and starts with "Rule:"), so we could then make the $val a link to the rule that caused it..?
        $event = $row['event'];
        echo"<tr><td> ".$row['timestamp']." </td><td>".$userName." </td><td>";
        if ($reason) {
            echo "<a href=\"/vesta/ShowReason.php/?event=",$event,"&reason=",$reason,"\">",$event,"</a>";
        } else {
            echo $event;    // No reason given
        }
        echo "</td></tr>";
    }
    echo "</table>";
}

?>
