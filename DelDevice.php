<?php
error_reporting(E_ALL); 
include "AppCmd.php";

ini_set('display_errors', '1');
$devId=$_GET['devId'];   // Get deviceId to delete from URL
$cmd= "removeDevice ".$devId;
echo "<html><head></head><body>";
echo AppCmd($cmd, false);
echo "<script type='text/javascript'>alert('",$devId," Removed')</script>"; // Show dialog box saying "Device Removed"
echo "<a href=\"/vesta/ShowAllDevices.php\">Show all devices</a>";
echo "</body></html>";
?>
