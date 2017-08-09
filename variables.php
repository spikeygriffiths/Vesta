<?php 
error_reporting(E_ALL); 
include "HubCmd.php";

$varsArray = [];
echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style></head>";
echo "<body>";
echo "<center><h1>Variables</h1>";
$varsList = HubCmd("vars", True);
$varsArray = explode(",", $varsList);
for ($index = 0; $index < count($varsArray); $index ++) {
    $varsArray[$index] = str_replace("'", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("(", "", $varsArray[$index]);
    $varsArray[$index] = str_replace(")", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("[", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("]", "", $varsArray[$index]);   # Tidy up strings, by removing Python decoration
}
echo "<table>";
echo "<tr><th>Name</th><th>Value</th></tr>";
for ($index = 0; $index < count($varsArray); $index += 2) {
    echo "<tr><td>",$varsArray[$index], "</td><td>", $varsArray[$index+1], "</td></tr>";
}
echo "</table><br>";
echo "<button type=\"button\" onclick=\"window.location.href='/index.php'\">Home</button><br><br>";
echo "</body></html>";
?>
