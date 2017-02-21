<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>IoT Hub</h1> ";
echo "Now: ", date('Y-m-d H:i:s'), "<br>";
$upT=shell_exec("uptime");
$ans=explode(" up ",$upT);
$ans=explode(',', $ans[1]);
$ans=$ans[0].", ".$ans[1];
echo "UpTime: ", $ans, "<br>";
$ps = shell_exec("ps ax");
$iotHubRunning = (strpos($ps, "hubapp.py") !== false);
if ($iotHubRunning) {
    echo "<button type=\"button\" onclick=\"window.location.href='devices.php'\">Devices</button><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='rules.php'\">Rules</button><br>";
    echo "</center>";
 } else {
    echo "<center><h2>IoT Hub stopped</h2></center>"; 
    $reason = shell_exec("tail --lines=15 /home/pi/hubapp/error_log");
    echo "<b>Last lines of error log;</b><br>",nl2br($reason);
}
echo "</body></html>";

?>
