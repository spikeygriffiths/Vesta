<?php 
session_start();
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
error_reporting(E_ALL); 
include "AppCmd.php";

$varsArray = [];
echo "<html><head>";
echo "<link rel=\"icon\" type=\"image/ico\" href=\"/favicon.ico\"/>";
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }</style></head>";
echo "<body>";
echo "<center><h1>Variables</h1>";
$varsList = AppCmd("vars", True);
$varsArray = explode(",", $varsList);
for ($index = 0; $index < count($varsArray); $index ++) {
    $varsArray[$index] = str_replace("'", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("(", "", $varsArray[$index]);
    $varsArray[$index] = str_replace(")", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("[", "", $varsArray[$index]);
    $varsArray[$index] = str_replace("]", "", $varsArray[$index]);   # Tidy up strings, by removing Python decoration
}
echo "<table>";
echo "<tr><th>Name</th><th>Value</th><th>At</th></tr>";
for ($index = 0; $index < count($varsArray); $index += 3) {
    echo "<tr><td>",$varsArray[$index], "</td><td>", $varsArray[$index+1], "</td><td>", $varsArray[$index+2], "</td></tr>";
}
echo "</table><br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";
?>
