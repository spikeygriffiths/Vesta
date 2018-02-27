<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$scheduleTxt = $_POST["scheduleTxt"];  // Get new schedule text from form
$day = $_GET['day']; // Get day name from URL
$type = $_GET['type'];
$db = DatabaseInit();
    $query = "UPDATE Schedules SET dailySchedule=\"".$dailySchedule."\" WHERE type=\"".$type."\" and day=\".$day."\""; # Update existing daily schedule
    echo "About to send ",$query, " to DB<br>";
    $count = $db->exec($query);
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Schedule.php/?type=\"",$type,"\">"; # Automatically go back to Schedule page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
echo "</body></html>";
?>
