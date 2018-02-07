<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 3px; padding-left: 10px; padding-right: 10px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</head><body>";
PageHeader("Variables");
$db = DatabaseInit();
ShowVars($db);
PageFooter();
echo "</body></html>";

function ShowVars($db)
{
    echo "<table>";
    echo "<tr><th>Name</th><th>Value</th><th>Age</th><th>Rules</th></tr>";
    $sth = $db->prepare("SELECT name FROM Variables");
    $sth->execute();
    $varCount = 0;
    while ($row = $sth->fetch()) {
        $names[$varCount++] = $row['name']; # Build array ready for sorting
    }
    sort($names, SORT_NATURAL | SORT_FLAG_CASE);  # Sort names
    for ($index  = 0; $index < $varCount; $index++) {
        $name = $names[$index];
        $sth = $db->prepare("SELECT value,timestamp FROM Variables where name=\"".$name."\"");
        $sth->execute();
        $row = $sth->fetch();
        $value = $row['value'];
        $timestamp = $row['timestamp'];
        echo "<tr><td>",$name,"</td><td>",$value,"</td><td>",ElapsedTime($timestamp),"</td>";
        echo "<td onclick=\"window.location.href='/vesta/rules.php/?item=",$name,"&type=vars'\">Rules</td></tr>";
    }
    echo "</table><br>";
}
?>
