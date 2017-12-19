<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</style></head>";
echo "<body>";
$table = $_GET['table'];
PageHeader("Database Table Stats for ".$table);
$db = DatabaseInit();
ShowTableStats($db, $table);
echo "<br>";
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/DatabaseStats.php'\">Database Stats</button><br><br>";
PageFooter();
echo "</body></html>";

function ShowTableStats($db, $table)
{
    echo "<table>";
    echo "<tr><th>Table</th><th>Entries</th></tr>";
    ShowStat($db, $table);
    echo "</table>";
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
