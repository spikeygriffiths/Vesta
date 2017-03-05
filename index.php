<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>IoT Hub</h1> <br>";
echo "Now: ", date('Y-m-d H:i:s'), "<br>";
ShowUpTime("/home/pi/hubapp/status.xml");
$ps = shell_exec("ps ax");
$iotHubRunning = (strpos($ps, "hubapp.py") !== false);
echo "<br>";
if ($iotHubRunning) {
    echo "<button type=\"button\" onclick=\"window.location.href='devices.php'\">Devices</button><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='rules.php'\">Rules</button><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='activity.php'\">Activity</button><br>";
    echo "</center>";
 } else {
    echo "<center><h2>IoT Hub stopped</h2></center>"; 
    $reason = shell_exec("tail --lines=15 /home/pi/hubapp/error_log");
    echo "<b>Last lines of error log;</b><br>",nl2br($reason);
}
echo "</body></html>";


function ShowUpTime($status)
{
    if (file_exists($status)) {
        $xml = simplexml_load_file($status) or die("Can't open ".$status);
    } else die("Can't find ".$status);
    echo "UpTime: " .  $xml->hub->uptime . "<br>";
}
?>
