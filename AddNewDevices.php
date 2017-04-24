<?php
include "HubCmd.php";

$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
echo "<html>";
echo "<head></head>";
echo "<body>";
echo "<center><h1>Add New Devices</h1> ";
echo "Now: ", date('Y-m-d H:i:s'), "<br><br>"; // Show page refreshing
echo HubCmd("open", false);
echo "<h3>Top tip - Make sure the new devices are all different types so you can distinguish them later!</h3><br><br>";
ShowNewDevices();
echo "<br><br><br><br>";
echo "<center><a href=\"/ShowAllDevices.php\">All Devices</a> </center><br>";
echo "<center><a href=\"/index.php\">Home</a> </center>";
echo "</body>";
echo "</html>";

function ShowNewDevices()
{
    $dir = "sqlite:/home/pi/hubapp/hubstuff.db";
    $db = new PDO($dir) or die("Cannot open database");
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    $numDevs = $result->fetchColumn();
    $foundNothing = True;
    for ($devIdx = 1; $devIdx < $numDevs; $devIdx++) {
        $result = $db->query("SELECT userName, manufName, modelName FROM devices WHERE devIdx=".$devIdx);
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        $userName = $fetch[userName];
        $manufName = $fetch[manufName];
        $modelName = $fetch[modelName];
        if (substr($userName, 0, 5)=="(New)") {
            $foundNothing = False;
            if (modelName != "") {
                echo "Found new ",$modelName," manufactured by: ",$manufName,"<br>";
            } else {
                echo "Found new device - requesting info...<br>";
            }
        }
    }
    if ($foundNothing) echo "Nothing so far...<br>";
}
?>
