<?php
include "database.php";
error_reporting(E_ALL);

ini_set('display_errors', '1');
$devKey=$_POST['devKey'];   // Get new device to add from form
$groupName = $_GET['groupName'];  // Get Group's user name from URL
$db = DatabaseInit();
$query = "SELECT devKeyList FROM Groups WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$sth = $db->prepare($query);
$sth->execute();
$sth->setFetchMode(PDO::FETCH_ASSOC);
$row =  $sth->fetch();
$devList = $row['devKeyList'];
if ($devList != "") {
    $devList .= ",";
}
$devList .= $devKey;
$query = "UPDATE Groups SET devKeyList=\"".$devList."\" WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$count = $db->exec($query);
if ($count == 1) {
    echo "<meta http-equiv=\"refresh\" content=\"1;url=/vesta/UpdateGroup.php/?groupName=",$groupName,"\"/>";
    echo "New device added to ",$groupName,"<br>";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
//echo "<a href=\"/vesta/UpdateGroup.php/?groupName=",$groupName,"\">",$groupName,"</a>";
echo "<a href='/vesta/UpdateGroup.php/?groupName=",$groupName,"'>Show Group</a>";
?>
