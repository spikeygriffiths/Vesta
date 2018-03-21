<?php
include "functions.php";
include "database.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
$user = $_SESSION['user_name'];
$db = DatabaseInit();
$appTitle = GetConfig("appTitle", "Vesta", $db);    // Assumes database.php has been included
echo "<title>",$appTitle," - ",$user,"</title>"; # For browser tab
echo "<center>";
$title = "<img src='vestaTitle.png' title=\"Vesta was the Roman goddess of hearth and home\" width=128 height=128>";
$rightBtn = "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/logout.php'\">Log Out</button><br><br>";
PageHeader($title, $rightBtn);
$ps = shell_exec("ps ax");
$appRunning = (strpos($ps, "vesta.py") !== false);
//echo "Current PHP version: ".phpversion()."<br>";
$statusPage = "status.html";
if ($appRunning) {
    echo "UpTime: ",AppCmd("uptime", True),"<br>";
    echo "<br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">Devices</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Groups.php'\">Groups</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/rules.php/?item=All'\">Rules</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/activity.php/?devKey=-1'\">Activity Log</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ToggleAway.php'\">";
    $db = DatabaseInit();
    $away = GetAppState("away", $db);
    if ($away == "True") {
        echo "Now Away - Click when Home";
    } else {
        echo "At Home - Change to Away";
    }
    echo "</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Variables.php'\">Variables</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/RequestStatus.php'\">Status</button>&nbsp&nbsp&nbsp";
    #echo "<button type=\"button\" onclick=\"window.location.href='/vesta/info.php'\">Send Info Command</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='https://docs.google.com/document/d/1BPCPYH9JV_Ekot3clXyhLmIPgkDzyd2aZhu5PGcCNKw/edit?usp=sharing'\">Documentation</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/DatabaseStats.php'\">Database Stats</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Config.php'\">Config</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ManageUsers.php'\">Manage users</button><br><br>";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/AppLog.php'\">Application Log</button>&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/log.php'\">Error Logs</button>&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=restart'\">Restart</button><br><br>";
    echo "</center>";
 } else {
    echo "<br>";
    echo "<center><h2>Vesta app stopped</h2></center>"; 
    $fragmentSize = 1500;
    $logName = "/home/pi/Vesta/err.log";
    if (!file_exists($logName)) {
        $logName = "/home/pi/Vesta/today.log";
    }
    $logHandle = fopen($logName, "r");
    $logSize = filesize($logName);
    fseek($logHandle, $logSize - $fragmentSize);    // Seek to near the end
    $logText = fread($logHandle, $fragmentSize);    // Read the last few bytes
    echo "..."; // Ellipsis before final log fragment
    echo nl2br($logText);   // NewLine To <br>
    echo "<br><br><button type=\"button\" onclick=\"window.location.href='/vesta/restart.php'\">Restart</button><br><br>";
}
echo "</body></html>";
?>
