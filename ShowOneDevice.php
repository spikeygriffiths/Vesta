<?php
error_reporting(E_ALL); 

echo "<html><head>";
echo "</head><body>";
$devIdx=$_GET['devIdx'];
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$username = DbGetItem("UserName", $devIdx,$db);
echo "<center><h1>",$username,"</h1></center>";
echo "<input type=\"size\" text=\"30\" name=\"UserName",$devIndex, "\" value=\"", $username, "\">";
echo "<form action=\"save_names.php\" method=\"post\">";
ShowDeviceInfo($db, $devIdx);
echo "<input type=\"submit\" value=\"Update Names\"></form>";
echo "<center><a href=\"index.php\">Home</a> </center>";
echo "</body></html>";

function  DbGetItem($item, $devIndex, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices LIMIT ".$devIndex.",1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowItem($item, $units, $devIndex, $db)
{
    $result = $db->query("SELECT value FROM Events WHERE item=\"".$item."\" AND devRowId=".$devIndex." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[value];
    if ($val != "") echo "<h3>",$item,"=",$val,$units,"</h3>"; else echo "<h3>",$item," N/A</h3>";
}

function ShowDeviceInfo($db, $devIndex)
{
    ShowItem("Battery", "%", $devIndex, $db);
    ShowItem("Temperature", "'C", $devIndex, $db);
    ShowItem("Presence", "", $devIndex, $db);
    ShowItem("Other", "", $devIndex, $db);
}
?>
