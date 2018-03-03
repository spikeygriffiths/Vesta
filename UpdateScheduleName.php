<?php
include "database.php";
include "functions.php";
include "header.php";
echo "</head><body>";
ini_set('display_errors', '1');
$username=$_GET['username'];
$oldSchedName =$_GET["oldSchedName"]; // Get old schedule name from URL
$schedName = $_POST["newSchedName"];  // Get new schedule name from form
$newSchedName = str_replace(" ", "_", $schedName);    # Ensure there are no spaces in schedule names by replacing them with underscores
$db = DatabaseInit();
if ($db) {
    $query = "UPDATE Schedules SET type=\"".$newSchedName."\" WHERE type=\"".$oldSchedName."\"";
    echo "About to send ",$query, " to DB<br>";
    $db->exec($query);
    echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Schedule.php/?username=",$username,"&type=",$newSchedName,"\"/>"; # Automatically go back to where we came from
} else {
    echo "Failed to get a handle onto the database<br>";
}
PageFooter();
echo "</body></html>";
?>
