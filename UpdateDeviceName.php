<?php
error_reporting(E_ALL);
include "database.php";

ini_set('display_errors', '1');
$devKey=$_GET['devKey'];
$newUserName = $_POST["UserName"];  // Get new user name from form
$db = DatabaseInit();
if ($db) {
    $oldUserName = GetDevItem("userName", $devKey,$db);
    echo "New name is:", $newUserName, " for device Id:",$devKey, " and old name was ", $oldUserName, "<br>";
    $query = "UPDATE Devices SET userName=\"".$newUserName."\" WHERE devKey=".$devKey;
    echo "About to send ",$query, " to DB<br>";
    $count = $db->exec($query);
    if ($count == 1) {
        UpdateRules($oldUserName, $newUserName, $db);    // Now go through the rules and make sure the old name is updated to the new
        echo "<meta http-equiv=\"refresh\" content=\"0;url=/ShowOneDevice.php/?devKey=",$devKey,"\"/>"; # Automatically go back to where we came from
        echo "New name saved";
    } else {
        echo "Update failed, with count of:", $count, "<br>";
    }
} else {
    echo "Failed to get a handle onto the database<br>";
}
echo "<a href=/ShowOneDevice.php/?devKey=",$devKey,">Show Device</a>"; # Let user go back to where we came from
?>
