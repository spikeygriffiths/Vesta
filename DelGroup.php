<?php
error_reporting(E_ALL);
include "database.php";

ini_set('display_errors', '1');
$groupName = $_GET['groupName'];  // Get Group's user name from URL
$db = DatabaseInit();
$query = "DELETE FROM Groups WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$count = $db->exec($query);
if ($count == 1) {
    echo "<meta http-equiv=\"refresh\" content=\"1;url=/vesta/Groups.php/\">";
    echo $groupName," successfully removed<br>";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
echo "<a href='/vesta/Groups.php''>Groups</a>";
?>
