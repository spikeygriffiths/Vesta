<?php
include "functions.php";
include "database.php";
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
echo "<center><h1>Add New Devices</h1> ";
echo "Now: ", date('Y-m-d H:i:s'), "<br>"; // Show page refreshing
echo AppCmd("open", False);
echo "<br><h3>Top tip - Make sure the new devices are all different types so you can distinguish them later!</h3><br><br>";
ShowNewDevices();
echo "<br><br><br><br>";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowAllDevices.php'\">All Devices</button><br><br>";
echo "<button class=\"buttonHome\" type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body>";
echo "</html>";

function ShowNewDevices()
{
    $db = DatabaseInit();
    $numDevs = GetDevCount($db);
    $foundNothing = True;
    for ($index = 0; $index < $numDevs; $index++) {
        $devKey = GetDevKey($index, $db);
        $userName = GetDevItem("userName", $devKey, $db);
        $manufName = GetDevItem("manufName", $devKey, $db);
        $modelName = GetDevItem("modelName", $devKey, $db);
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
