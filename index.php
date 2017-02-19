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
echo "</center>";
$ps = shell_exec("ps ax");
$iotHubRunning = (strpos($ps, "hubapp.py") !== false);
if ($iotHubRunning) {
    //echo "<button type=\"button\" onclick=\"alert('Not working yet...')\">Add new devices</button><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='AddNewDevices.php'\">Add new devices</button><br>";
    ShowDevices("/home/pi/hubapp/usernames.txt");
    echo  "<button type=\"button\" onclick=\"window.location.href='rules.php'\">Rules</button><br>";
 } else {
    echo "<center><h2>IoT Hub stopped</h2></center>"; 
    $reason = shell_exec("tail --lines=15 /home/pi/hubapp/error_log");
    echo "<b>Last lines of error log;</b><br>",nl2br($reason);
}
echo "</body></html>";

function ShowDevices($filename, $key)
{
    $handle = fopen($filename, "r");
    if ($handle) {
        $index = 0;
        while (!feof($handle)) {
            $line = fgets($handle);
            // Need to parse Python list - might be better to have special file, or even an API(!)
            echo "<input type=\"text\" size=\"40\" name=\"username", $index, "\" value=\"", $line, "\"><br>";
            $index++;
        }
        fclose($handle); 
    } else echo "No devices!<br>"; // Else error opening file
}

?>
