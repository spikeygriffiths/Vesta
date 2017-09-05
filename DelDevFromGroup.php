<?php
error_reporting(E_ALL);
include "database.php";

ini_set('display_errors', '1');
$devKey=$_GET['devKey'];   // Get new device to add from URL
$groupName = $_GET['groupName'];  // Get Group's user name from URL
$db = DatabaseInit();
$query = "SELECT devKeyList FROM Groups WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$sth = $db->prepare($query);
$sth->execute();
$sth->setFetchMode(PDO::FETCH_ASSOC);
$row =  $sth->fetch();
$devList = $row['devKeyList'];
$devs = explode(",", $devList);
while (($item = array_search($devKey, $devs)) !== false) {  // Remove all occurrences of devKey
    unset($devs[$item]);
}
$devList = implode(",", $devs);
$query = "UPDATE Groups SET devKeyList=\"".$devList."\" WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$count = $db->exec($query);
if ($count == 1) {
    echo "<meta http-equiv=\"refresh\" content=\"1;url=/vesta/UpdateGroup.php/?groupName=",$groupName,"\"/>";
    echo "New device added to ",$groupName,"<br>";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
echo "<a href='/vesta/UpdateGroup.php/?groupName=",$groupName,"'>Show Group</a>";
?>
