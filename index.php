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
    echo "<button type=\"button\" onclick=\"window.location.href='Groups.php'\">Groups</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='rules.php'\">Rules</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='activity.php'\">Events</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='log.php'\">Show Debugging Log</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='info.php'\">Send Info Command</button><br><br>";
    echo "<br><br>";
    echo "<a href='https://docs.google.com/document/d/1BPCPYH9JV_Ekot3clXyhLmIPgkDzyd2aZhu5PGcCNKw/edit?usp=sharing' target='_blank'>Documentation</a><br><br>";
    echo "</center>";
 } else {
    echo "<br>";
    echo "<center><h2>IoT Hub stopped</h2></center>"; 
    //$reason = shell_exec("tail --lines=20 /home/pi/hubapp/today.log");
    //echo "<b>Last lines of today's hub log;</b><br>",nl2br($reason);
    $fragmentSize = 1000;
    $logName = "/home/pi/hubapp/today.log";
    $logHandle = fopen($logName, "r");
    $logSize = filesize($logName);
    fseek($logHandle, $logSize - $fragmentSize);    // Seek to near the end
    $logText = fread($logHandle, $fragmentSize);    // Read the last few bytes
    echo "..."; // Ellipsis before final log fragment
    echo nl2br($logText);   // NewLine To <br>
    echo "<br><br><button type=\"button\" onclick=\"window.location.href='restart.php'\">Restart</button><br><br>";
}
echo "</body></html>";
?>
