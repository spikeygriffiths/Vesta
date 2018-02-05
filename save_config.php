<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$value = $_POST["valueTxt"];  // Get new value text from form
$item = $_GET['item']; // Get item name from URL
$db = DatabaseInit();
if ($db) {
    if ($item != "NewItem") { // If item exists
        if ($value != "") {
            $query = "UPDATE Config SET value=\"".$value."\" WHERE item=\"".$item."\""; # Update existing value
        } else {
            $query = "DELETE FROM Config WHERE item=\"".$item."\"";  # Remove item if value is empty
        }
    } else { // New Item requested
        $query = "INSERT INTO Config (item) VALUES(\"".$value."\")";  # Add new configuration item (named $value), with empty value
    }
    echo "About to send ",$query, " to DB<br>";
    $count = $db->exec($query);
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Config.php/>"; # Automatically go back to Config page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
echo "</body></html>";
?>
