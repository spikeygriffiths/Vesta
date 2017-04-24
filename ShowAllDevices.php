<?php 
//error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style></head>";
echo "<body>";
echo "<center><h1>Devices</h1> ";
echo "<button type=\"button\" onclick=\"window.location.href='AddNewDevices.php'\">Add new devices</button><br><br>";
//print_r (PDO::getAvailableDrivers()); echo("<br>"); // Shows whether you have SQLite for PDO installed
ShowDevices();
echo "<br><a href=\"/index.php\">Home</a></center>";
echo "</body></html>";

function GetDevIdx($index, $db)
{
    $item = "devKey";
    $result = $db->query("SELECT ".$item." from Devices LIMIT 1 OFFSET ".$index);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function DevGetItem($item, $devKey, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devKey=".$devKey);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function  DevGetStatus($item, $devKey, $db)
{
    $result = $db->query("SELECT ".$item." FROM Status WHERE devKey=".$devKey);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function ShowDevStatus($item, $devKey, $db)
{
    $val = DevGetStatus($item, $devKey,$db);
    if ($val != null) {
        echo "<td>$val</td>";
    } else {
        echo "<td>N/A</td>";
    }
}

function ShowEvent($devKey, $db)
{
    $result = $db->query("SELECT event FROM Events WHERE devKey=".$devKey." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[event];
    if ($val != "") echo "<td>",$val,"</td>"; else echo "<td>N/A</td>";
}

function ShowDevices()
{
    $dir = "sqlite:/home/pi/hubapp/hubstuff.db";
    $db = new PDO($dir) or die("Cannot open database");
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    $numDevs = $result->fetchColumn();
    echo "<table>";
    echo "<tr><th>Name</th><th>Battery %</th><th>Signal %</th><th>Presence</th><th>Notes</th></tr>";
    for ($index = 0; $index < $numDevs; $index++) {
        $devKey = GetDevIdx($index, $db);
        echo "<tr>";
        $username = DevGetItem("userName", $devKey, $db);
        echo "<td><a href=\"ShowOneDevice.php/?devKey=",$devKey,"\">",$username,"</a></td>";
	    ShowDevStatus("battery", $devKey, $db);
	    ShowDevStatus("signal", $devKey, $db);
  	    ShowDevStatus("presence", $devKey, $db);
        ShowEvent($devKey, $db);
        echo "</tr>";
    }
    echo "</table>";
}
?>
