<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
include "database.php";

echo "<html><body>";
$userId = $_GET['userId'];

$db = DatabaseInit();
if ($db) {
    if ($userId >= 0) {
        $query = "DELETE FROM Users WHERE id=".$userId;  # Remove selected user
    }
    $count = $db->exec($query);
}
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/ManageUsers.php\"/>"; # Automatically go to ManageUsers page
echo "<p><center><a href=\"/vesta/index.php\">Home</a></center>"; # Shouldn't be needed (or indeed visible!)
echo "</body></html>";
?>
