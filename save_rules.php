<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$ruleTxt = $_POST["ruleTxt"];  // Get new rule text from form
$ruleId = $_GET['ruleId'];
$item = $_GET['item'];

$db = DatabaseInit();
if ($db) {
    if ($ruleId != -1) {
        if ($ruleTxt != "") {
            $query = "UPDATE Rules SET rule=\"".$ruleTxt."\" WHERE rowid=".$ruleId; # Update existing rule
        } else {
            $query = "DELETE FROM Rules WHERE rowid=".$ruleId;  # Remove empty rule
        }
    } else {
        $query = "INSERT INTO Rules VALUES(\"".$ruleTxt."\")";  # Add new rule
    }
    echo "About to send ",$query, " to DB<br>";
    $count = $db->exec($query);
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/rules.php/?item=", $item, "\"/>"; # Automatically go to rules page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>";
echo "</body></html>";
?>
