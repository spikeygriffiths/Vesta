<?php 
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$dbTime=$_GET['dbTime'];
$titleTime=$_GET['titleTime'];
if (empty($dbTime)) {
    $dbTime = "date('now', 'start of day')";
    $titleTime = "Today";
}
$devIdx=$_GET['devIdx'];
if (empty($devIdx)) {
    $devIdx = -1;   // Means "Get all devices"
}
echo "<center><h1>Activity</h1>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
// See if the time needs to be adjusted
echo "<form action='/SelectActivityTime.php' method='post'>";
echo "<p>Show events from:<select id='timePeriod' name='timePeriod'>";
echo "<option value='today'>Today</option>";
echo "<option value='yesterday'>Yesterday onwards</option>";
echo "<option value='week'>Last week</option>";
echo "<option value='month'>Last 30 days</option>";
echo "</select>";
// Now see if user wants to select device
echo "<p>Show events for:<select id='devIdx' name='devIdx'>";
echo "<option value=-1>All devices</option>";
$result = $db->query("SELECT COUNT(*) FROM Devices");
$numDevs = $result->fetchColumn();
for ($idx=0; $idx<$numDevs; $idx++) {
    $userName = DbGetItem("userName", $idx, $db);
    echo "<option value='",$idx,"'>",$userName,"</option>";
}
echo "</select><p>";
echo "<input type='submit' name='submit'/>";
echo "</form>";
ShowActivity($db, $dbTime, $titleTime, $devIdx);
echo "<br><a href=\"/index.php\">Home</a></center>";
echo "</body></html>";

function  DbGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowActivity($db, $dbTime, $titleTime, $devIdx)
{
    //echo "Show Activity for devIdx:", $devIdx, "<br>";    // Debugging
    if ($devIdx==-1) {
        echo "<h3>Showing all activity from ",$titleTime,"</h3>";
        $sth = $db->prepare("SELECT * FROM Events WHERE timestamp > ".$dbTime);
    } else {
        $userName = DbGetItem("userName", $devIdx, $db);
        echo "<h3>Showing activity for ",$userName," from ",$titleTime,"</h3>";
        $sth = $db->prepare("SELECT * FROM Events WHERE devIdx=".$devIdx." AND timestamp > ".$dbTime);
    }
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $userName = DbGetItem("userName", $row['devIdx'],$db);        // Use $row['devIdx'] as key into Devices table to get $userName
        echo"<tr><td> ".$row['timestamp']." </td><td>".$userName." </td><td> ".$row['event']." </td></tr>";
    }
    echo "</table>";
}

?>
