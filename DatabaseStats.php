<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</style></head>";
echo "<body>";
PageHeader("Database Stats");
$db = DatabaseInit();
ShowAllStats($db);
echo "<br>";
PageFooter();
echo "</body></html>";

function ShowAllStats($db)
{
    $dbSize = GetDbFileSize();
    $numDevs = GetDevCount($db);
    $tablesquery = $db->prepare("SELECT name FROM sqlite_master WHERE type='table';");  # Get the names of all the tables in the database
    $tablesquery->execute();
    $dbTableInfo = array();
    while ($table =  $tablesquery->fetch()) {
        $name = $table['name'];
        $dbTableInfo[] = array($name, GetCount($db, $name));
    }
    usort($dbTableInfo, "BySize");  # Sort by size (element 1 of each array)
    echo "<table>";
    echo "<tr><th>Table</th><th>Entries</th></tr>";
    foreach ($dbTableInfo as $info) {
        ShowStat($db, $info[0]);
    }
    echo "</table>";
    echo "<br>(Database file: ",number_format($dbSize / (1024*1024), 2, '.', ''),"MB for ",$numDevs," devices=",number_format(($dbSize/($numDevs*1024)), 0, '.', ''),"KB per device)<br>";
}

function BySize($a, $b) {   # Sort by size (element 1 of each array)
    return ($a[1] < $b[1]);
}

function ShowStat($db, $table)
{
    $entries = GetCount($db, $table);
    if ($entries >= 100) {  # Don't bother showing small tables
        echo "<tr>";
        echo "<td><a href=\"/vesta/DbTableStats.php/?table=",$table,"\">",$table,"</a></td>";
        echo "<td>",$entries,"</td></tr>";
    }
}

?>
