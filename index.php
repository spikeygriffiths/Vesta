<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>IoT Hub</h1> ";
echo "Now: ", date('Y-m-d H:i:s'); // Add UpTime for hubapp
echo "</center>";
$ps = shell_exec("ps ax");
$iotHubRunning = (strpos($ps, "hubapp.py") !== false);
if ($iotHubRunning) {
    //echo "<button type=\"button\" onclick=\"alert('Not working yet...')\">Add new devices</button><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='AddNewDevices.php'\">Add new devices</button><br>";
    ShowDevices("/home/pi/hubapp/devices.txt", "UserName");
    ShowRules("/home/pi/hubapp/rules.txt", "if");
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
        while (!feof($handle)) {
            $line = fgets($handle);
            // Need to parse Python list - might be better to have special file, or even an API(!)
            if (strpos($line, $key) !== false) {
                echo $line, "<br>";
            }
            //$arr[$index++] = $line;
        }
        echo "<br>";
        fclose($handle); 
    } else echo "No devices!<br>"; // Else error opening file
}

function ShowRules($filename, $key)
{
    $arr = array();
    $index = 0;
    $handle = fopen($filename, "r");
    if ($handle) {
        echo "<table border=&quot;1&quot;>";
        while (!feof($handle)) {
            $line = fgets($handle);
            while (($lt = strpos($line, "<")) !== false) {
                $line = str_replace("<", "&lt;", $line);
            }
            if (strpos($line, $key) !== false) {
                echo "<tr><td>", $line, "</tr></td>";
            }
            $arr[$index++] = $line;
        }
        echo "</table>";
        fclose($handle); 
    } else echo "No rules defined<br>"; // Else error opening file
}
?>
