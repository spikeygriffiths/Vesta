<?php
# ToggleAway.php
# Flips "away" variable between True and False
error_reporting(E_ALL); 
include "database.php";

$db = DatabaseInit();
$away = GetAppState("away", $db);
if ($away ==  "False") $away = "True"; else $away = "False";    // Flip value
SetAppState("away", $away, $db);
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/vesta.php\"/>"; # Automatically re-display home page (assumes we've come from there)
//echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
?>
