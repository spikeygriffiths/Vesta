<?php 
include "functions.php";
$varsArray = [];
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 3px; padding-left: 10px; padding-right: 10px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style>";
echo "</head><body>";
PageHeader("Variables");
$varsList = AppCmd("vars", True);   # NB Already alphabetically sorted from Python app
$varsArray = explode(",", $varsList);
for ($index = 0; $index < count($varsArray); $index ++) {
    $varsArray[$index] = str_replace("\n", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("'", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("(", "", $varsArray[$index]);
    $varsArray[$index] = str_replace(")", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("[", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("]", "", $varsArray[$index]);   # Tidy up strings, by removing Python decoration
}
echo "<table>";
echo "<tr><th>Name</th><th>Value</th><th>Age</th><th>Rules</th></tr>";
for ($index = 0; $index < count($varsArray); $index += 3) {
    echo "<tr><td>",$varsArray[$index], "</td><td>", $varsArray[$index+1], "</td><td>",ElapsedTime($varsArray[$index+2]), "</td><td onclick=\"window.location.href='/vesta/rules.php/?item=",$varsArray[$index],"&type=vars'\">Rules</td></tr>";
}
echo "</table><br>";
PageFooter();
echo "</body></html>";
?>
