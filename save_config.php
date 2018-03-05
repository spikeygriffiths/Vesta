<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$value = $_POST["valueTxt"];  // Get new value text from form
$item = $_GET['item']; // Get item name from URL
$db = DatabaseInit();
SetConfig($item, $value, $db);
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Config.php/>"; # Automatically go back to Config page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
echo "</body></html>";
?>
