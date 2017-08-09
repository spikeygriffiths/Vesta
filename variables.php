<<?php 
error_reporting(E_ALL); 
include "HubCmd.php";

$varsArray = [];
echo "<html><head>";
echo "</head><body>";
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
echo "<tr><th>Variable</th><th>Value</th></tr>";
for ($index = 0; $index < count($varsArray); $index += 2) {
    echo "<tr><td>",$varsArray[$index], "</td><td>", $varsArray[$index+1], "</td></tr>";
}
echo "</table>";
echo "<center><br><a href=\"/index.php\">Home</a> </center>";
echo "</body></html>";
?>
