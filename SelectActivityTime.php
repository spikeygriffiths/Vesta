<?php
error_reporting(E_ALL);

//echo "Got here!";
$timePeriod=$_POST["timePeriod"];
if ($timePeriod=="today") {
    $dbTime = "date('now', 'start of day')";
    $titleTime = "Today";
} else if ($timePeriod=="yesterday") {
    $dbTime = "date('now', '-1 day')";
    $titleTime = "Last 2 days";
} else if ($timePeriod=="week") {
    $dbTime = "date('now', '-7 days')";
    $titleTime = "Last week";
} else if ($timePeriod=="month") {
    $dbTime = "date('now', '-31 days')";
    $titleTime = "Last month";
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/activity.php/?dbTime=",$dbTime,"&titleTime=",$titleTime,"\"/>";
?>
