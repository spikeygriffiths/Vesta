<?php
include "database.php";
include "header.php";
echo "</head><body>";
ini_set('display_errors', '1');
$devKey=$_GET['devKey'];
$userName = $_POST["UserName"];  // Get new user name from form
$newUserName = str_replace(" ", "_", $userName);    # Ensure there are no spaces in usernames by replacing them with underscores
$db = DatabaseInit();
if ($db) {
    $oldUserName = GetDevItem("userName", $devKey,$db);
    echo "New name is:", $newUserName, " for device Id:",$devKey, " and old name was ", $oldUserName, "<br>";
    $query = "UPDATE Devices SET userName=\"".$newUserName."\" WHERE devKey=".$devKey;
    echo "About to send ",$query, " to DB<br>";
    $count = $db->exec($query);
    if ($count == 1) {
        UpdateRules($oldUserName, $newUserName, $db);    // Now go through the rules and make sure the old name is updated to the new
        echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/ShowOneDevice.php/?devKey=",$devKey,"\"/>"; # Automatically go back to where we came from
        echo "New name saved";
    } else {
        echo "Update failed, with count of:", $count, "<br>";
    }
} else {
    echo "Failed to get a handle onto the database<br>";
}
echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'>Show Device</button><br><br>"; # Let user go back to where we came from
echo "<button class=\"buttonHome\" type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";
?>
