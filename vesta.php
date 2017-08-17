<?php 
session_start();
error_reporting(E_ALL); 
include "HubCmd.php";
include "database.php";
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/index.php\"/>"; # Automatically go to index if we're not logged in

echo "<html><head>";
echo "<link rel=\"icon\" type=\"image/ico\" href=\"/favicon.ico\"/>";   # Not sure if this is necessary, but does no harm...
echo "</head><body>";
echo "<center><img src='vestaTitle.png' width=128 height=128><br>";
echo "Now: ", date('Y-m-d H:i:s'), "<br>";
$ps = shell_exec("ps ax");
$appRunning = (strpos($ps, "vesta.py") !== false);
echo "Current PHP version: ".phpversion()."<br>";
$statusPage = "status.html";
if ($appRunning) {
    echo "UpTime: ",HubCmd("uptime", True),"<br>";
    echo "<br>";
    echo "<button type=\"button\" onclick=\"window.location.href='ShowAllDevices.php'\">Devices</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='Groups.php'\">Groups</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='rules.php/?item=All'\">Rules</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='activity.php'\">Activity Log</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='ToggleAway.php'\">";
    $db = DatabaseInit();
    $away = GetAppState("away", $db);
    if ($away == "True") {
        echo "Now Away - Click when Home";
    } else {
        echo "At Home - Change to Away";
    }
    echo "</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='variables.php'\">Variables</button><br><br>";
    if (file_exists($statusPage)) {
        echo "<button type=\"button\" onclick=\"window.location.href='$statusPage'\">Status</button><br><br>";
    }
    #echo "<button type=\"button\" onclick=\"window.location.href='log.php'\">Show Debugging Log</button><br><br>";
    #echo "<button type=\"button\" onclick=\"window.location.href='info.php'\">Send Info Command</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='https://docs.google.com/document/d/1BPCPYH9JV_Ekot3clXyhLmIPgkDzyd2aZhu5PGcCNKw/edit?usp=sharing'\">Documentation</button><br><br>";
    echo "<button type=\"button\" onclick=\"window.location.href='logout.php'\">Log Out</button><br><br>";
    echo "</center>";
 } else {
    echo "<br>";
    echo "<center><h2>Vesta app stopped</h2></center>"; 
    //$reason = shell_exec("tail --lines=20 /home/pi/hubapp/today.log");
    //echo "<b>Last lines of today's hub log;</b><br>",nl2br($reason);
    $fragmentSize = 1500;
    $logName = "/home/pi/hubapp/hubout.log";
    if (!file_exists($logName)) {
        $logName = "/home/pi/hubapp/today.log";
    }
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
