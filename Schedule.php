<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
$type = $_GET['type'];
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 3px; padding-left: 10px; padding-right: 10px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</head><body>";
PageHeader("Schedule for ".$type);
$db = DatabaseInit();
ShowSchedule($db, $type);
PageFooter();
echo "</body></html>";

function ShowSchedule($db, $type)
{
    echo "<table>";
    echo "<tr><th>Day</th><th>Schedule</th></tr>";
    $sth = $db->prepare("SELECT * FROM Schedules WHERE type=\"".$type."\"");
    $sth->execute();
    while ($row = $sth->fetch()) {
        $dayOfWeek = $row['day'];
        $schedule = $row['dailySchedule'];
        echo "<tr><td>",$dayOfWeek,"</td><td>",$schedule,"</td>";
    }
    echo "</table><br>";
}
?>
