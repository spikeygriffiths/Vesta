<?php 
//error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style></head>";
echo "<body>";
echo "<center><h1>Devices</h1> ";
echo "<button type=\"button\" onclick=\"window.location.href='AddNewDevices.php'\">Add new devices</button><br>";
echo "</center>";
print_r (PDO::getAvailableDrivers()); echo("<br>"); // Shows whether you have SQLite for PDO installed
ShowDevices();
echo "<center><a href=\"/index.php\">Home</a> </center>";
echo "</body></html>";

function  DbGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function TableElement($item, $units, $devIdx, $db)
{
    $result = $db->query("SELECT value FROM Events WHERE item=\"".$item."\" AND devIdx=".$devIdx." ORDER BY TIMESTAMP DESC LIMIT 1");
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    $val = $fetch[value];
    if ($val != "") echo "<td>",$val,$units,"</td>"; else echo "<td>N/A</td>";
}

function ShowDevices()
{
    $dir = "sqlite:/home/pi/hubapp/hubstuff.db";
    $db = new PDO($dir) or die("Cannot open database");
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    $numDevs = $result->fetchColumn();
    echo "<table>";
    echo "<tr><th>Name</th><th>Battery %</th><th>Temperature (C)</th><th>Presence</th><th>Notes</th></tr>";
    for ($devIdx = 0; $devIdx < $numDevs; $devIdx++) {
        echo "<tr>";
        $username = DbGetItem("userName", $devIdx, $db);
        echo "<td><a href=\"ShowOneDevice.php/?devIdx=",$devIdx,"\">",$username,"</a></td>";
	    TableElement("Battery", "%", $devIdx, $db);
	    TableElement("Temperature", "'C", $devIdx, $db);
	    TableElement("Presence", "", $devIdx, $db);
	    TableElement("Other", "", $devIdx, $db);
        echo "</tr>";
    }
    echo "</table>";
}
?>
