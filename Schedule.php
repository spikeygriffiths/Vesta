<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
$type = $_GET['type'];
$devKey = $_GET['devKey'];
echo "</head><body>";
$db = DatabaseInit();
$numSchedules = GetCount($db, "Schedules", "day=\"Sun\"");    # Get number of schedules
$username = GetDevItem("userName", $devKey,$db);
if ($numSchedules > 1) {
    $rightBtn = "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=delSchedule ".$type."'\">Remove</button>";
} else $rightBtn = "";
PageHeader("Schedule for ".$type, $rightBtn);

// See if the schedule needs changing
echo "<form action='/vesta/SelectSchedule.php/?devKey=".$devKey."' method='post'>";
echo "<p>Select Schedule from:<select id='type' name='type'>";
$sth = $db->prepare("SELECT type FROM Schedules WHERE day=\"Sun\"");
$sth->execute();
while ($row = $sth->fetch()) {
    $option = $row['type'];
    echo "<option value='",$option,"'>",$option,"</option>";
}
echo "</select>";
echo "<input type='submit' name='submit'/>";
echo "</form>";

ShowSchedule($db, $type);
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ChangeScheduleName.php/?devKey=",$devKey,"&type=",$type,"'\">Change Schedule Name</button>&nbsp&nbsp&nbsp";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=newSchedule New_Schedule'\">New Schedule</button><br><br>"; // Button here to create new schedule in database
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=getSchedule ",$username,"'\">Get Schedule<br/>From ",$username,"</button>&nbsp&nbsp&nbsp";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setSchedule ",$username," ",$type,"'\">Set Schedule<br>On ",$username,"</button><br><br>"; // Button here to push new schedule to device
//echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=getAttr ",$username," 0201 0020'\">Get StartOfWeek<br>On ",$username,"</button>&nbsp&nbsp&nbsp&nbsp";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'\">",$username,"</button><br><br>";
PageFooter();
echo "</body></html>";

function ShowSchedule($db, $type)
{
    $dows=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];
    $sth = $db->prepare("SELECT * FROM Schedules WHERE type=\"".$type."\"");
    $sth->execute();
    while ($row = $sth->fetch()) {
        $day = $row['day'];
        $dayIndex = array_search($day, $dows);
        $scheduleTxts[$dayIndex] = $row['dailySchedule']; # Build array in day of week ordering
    }
    echo "<table>";
    for ($index = 0; $index < 7; $index++) { // 7 days in a week
        $day = $dows[$index];
        $scheduleTxt = $scheduleTxts[$index];
        echo "<tr><td>",$day,"</td><td>";
        echo "<form action=\"/vesta/save_schedule.php/?type=",$type,"&day=",$day,"&username=",$username,"\"method=\"post\">";
        echo "<input type=\"text\" size=\"50\" name=\"scheduleTxt\" value=\"", $scheduleTxt, "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
        echo "</td></tr>";
    }
    echo "</table><br>";
}
?>

