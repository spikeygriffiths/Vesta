<?php
include "AppCmd.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
ini_set('display_errors', '1');
$devId=$_GET['devId'];   // Get deviceId to delete from URL
$cmd= "removeDevice ".$devId;
echo AppCmd($cmd, false);
echo "<script type='text/javascript'>alert('",$devId," Removed')</script>"; // Show dialog box saying "Device Removed"
echo "<a href=\"/vesta/ShowAllDevices.php\">Show all devices</a>";
echo "</body></html>";
?>
