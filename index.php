<?php 
error_reporting(E_ALL); 
include "HubCmd.php";

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>IoT Hub</h1>";
echo "Now: ", date('Y-m-d H:i:s'), "<br>";
$ps = shell_exec("ps ax");
$iotHubRunning = (strpos($ps, "hubapp.py") !== false);
if ($iotHubRunning) {
    echo "UpTime: ",HubCmd("uptime", True),"<br>";
    echo "<br>";
    echo "<button type=\"button\" onclick=\"window.location.href='ShowAllDevices.php'\">Devices</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='rules.php'\">Rules</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='activity.php'\">Events</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='log.php'\">Show Debugging Log</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='info.php'\">Send Info Command</button><br><br>";
    echo "</center>";
 } else {
    echo "<br>";
    echo "<center><h2>IoT Hub stopped</h2></center>"; 
    $reason = shell_exec("tail --lines=20 /home/pi/hubapp/hub.log");
    echo "<b>Last lines of hub.log;</b><br>",nl2br($reason);
}
echo "</body></html>";
?>
