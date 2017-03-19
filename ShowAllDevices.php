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
echo "<form action=\"save_names.php\" method=\"post\">";
print_r (PDO::getAvailableDrivers()); echo("<br>"); // Shows whether you have SQLite for PDO installed
ShowDevices();
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

function TableElement($item, $units, $devIndex, $db)
{
    $result = $db->query("SELECT value FROM Events WHERE item=\"".$item."\" AND devRowId=".$devIndex." ORDER BY TIMESTAMP DESC LIMIT 1");
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
    for ($devIndex = 0; $devIndex < $numDevs; $devIndex++) {
        echo "<tr>";
        $username = DbGetItem("UserName", $devIndex, $db);
        echo "<td><a href=\"ShowOneDevice.php/?devIdx=",$devIndex,"\">",$username,"</a></td>";
	    TableElement("Battery", "%", $devIndex, $db);
	    TableElement("Temperature", "'C", $devIndex, $db);
	    TableElement("Presence", "", $devIndex, $db);
	    TableElement("Other", "", $devIndex, $db);
        echo "</tr>";
    }
    echo "</table>";
    echo "<input type=\"hidden\" name=\"numNames\", value=\"",$numDevs,"\">";
}
?>
