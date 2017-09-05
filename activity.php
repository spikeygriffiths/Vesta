<?php 
session_start();
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
include "database.php";
error_reporting(E_ALL); 

echo "<html><head>";
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$dbTime = $_GET['dbTime'];
$titleTime = $_GET['titleTime'];
if (empty($titleTime) || empty($dbTime)) {
    $dbTime = "date('now', 'start of day')";
    $titleTime = "Today";
}
$devKey = $_GET['devKey'];
echo "<center><h1>Activity</h1>";
$db = DatabaseInit();
// See if the time needs to be adjusted
echo "<form action='/vesta/SelectActivityTime.php/?devKey=".$devKey."' method='post'>";
echo "<p>Show events from:<select id='timePeriod' name='timePeriod'>";
echo "<option value='today'>Today</option>";
echo "<option value='yesterday'>Yesterday onwards</option>";
echo "<option value='week'>Last week</option>";
echo "<option value='month'>Last 30 days</option>";
echo "</select>";
// Now see if user wants to select device
/*echo "<p>Show events for:<select id='devKey' name='devKey'>";
echo "<option value=-1>All devices</option>";
$numDevs = GetDevCount($db);
for ($idx=0; $idx<$numDevs; $idx++) {
    $deviceKey = GetDevKey($idx, $db);
    $userName = GetDevItem("userName", $deviceKey, $db);
    echo "<option value='",$idx,"'>",$userName,"</option>";
}
echo "</select><p>";*/
echo "<input type='submit' name='submit'/>";
echo "</form>";
ShowActivity($db, $dbTime, $titleTime, $devKey);
echo "<br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowActivity($db, $dbTime, $titleTime, $devKey)
{
    if ($devKey==-1) {
        echo "<h3>Showing all activity from ",$titleTime,"</h3>";
        $sth = $db->prepare("SELECT * FROM Events WHERE timestamp > ".$dbTime);
    } else {
        $userName = GetDevItem("userName", $devKey, $db);
        echo "<h3>Showing activity for ",$userName," from ",$titleTime,"</h3>";
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
