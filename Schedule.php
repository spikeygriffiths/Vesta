<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
$type = $_GET['type'];
$username = $_GET['username'];
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 3px; padding-left: 10px; padding-right: 10px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</head><body>";
PageHeader("Schedule for ".$type);
$db = DatabaseInit();
ShowSchedule($db, $type);
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setSchedule ",$username,"&type=\",$type,"\"'\">Set Schedule</button>&nbsp&nbsp&nbsp"; // Button here to push new schedule to device
PageFooter();
echo "</body></html>";

function ShowSchedule($db, $type)
{
    echo "<table>";
    echo "<tr><th>Day</th><th>Schedule</th></tr>";
    $sth = $db->prepare("SELECT * FROM Schedules WHERE type=\"".$type."\"");
    $sth->execute();
    while ($row = $sth->fetch()) {
        $day = $row['day'];
        $scheduleTxt = $row['dailySchedule'];
        echo "<tr><td>",$day,"</td><td>";
        echo "<form action=\"/vesta/save_schedule.php/?type=\"",$type,"\"&day=\"", $day, "\"\" method=\"post\">";
        echo "<input type=\"text\" size=\"50\" name=\"scheduleTxt\" value=\"", $scheduleTxt, "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
        echo "</td></tr>";
    }
    echo "</table><br>";
}
?>

