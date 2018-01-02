<?php
# configChange.php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "AppCmd.php";
include "database.php";
$db = DatabaseInit();

echo "<html><body>";
$devKey=$_GET['devKey'];
$field=$_GET['field'];
$min = $_POST["min"];  // Get new values from form
$max = $_POST["max"];
$delta = $_POST["delta"];

$db = DatabaseInit();
if ($db) {
    $query = "UPDATE Devices SET ".$field."=\"".$min.",".$max.",".$delta."\" WHERE devKey=".$devKey; # Update existing configuration
    echo "About to send ",$query, " to DB<br>"; # For debugging only
    $db->exec($query);
    $cmd = "config ".$devKey." ".$field;
    AppCmd($cmd, False);    # Send command to app to tell it to use the new configuration item
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/DevConfig.php/?devKey=",$devKey,"\"/>"; # Automatically go back to Device Configuration page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";   # Shouldn't be needed
echo "</body></html>";
?>
