<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$scheduleTxt = $_POST['scheduleTxt'];  // Get new schedule text from form
$day = $_GET['day']; // Get day name from URL
$type = $_GET['type'];
$devKey = $_GET['devKey'];
$db = DatabaseInit();
$username = GetDevItem("userName", $devKey,$db);
$query = "UPDATE Schedules SET dailySchedule=\"".$scheduleTxt."\" WHERE type=\"".$type."\" AND day=\"".$day."\""; # Update existing daily schedule
echo "About to send ",$query," to DB<br>";
$db->exec($query);
SetConfig("HeatingSchedule", $type, $db);
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Schedule.php/?type=",$type,"&devKey=",$devKey,"\"/>"; # Automatically go back to Schedule page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
echo "</body></html>";
?>
