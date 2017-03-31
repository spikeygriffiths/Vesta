<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$devIdx=$_GET['devIdx'];   // Get new device to add from URL
$groupName = $_GET['groupName'];  // Get Group's user name from URL
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$query = "SELECT devIdxList FROM Groups WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$sth = $db->prepare($query);
$sth->execute();
$sth->setFetchMode(PDO::FETCH_ASSOC);
$row =  $sth->fetch();
$devList = $row['devIdxList'];
$devs = explode(",", $devList);
while (($item = array_search($devIdx, $devs)) !== false) {  // Remove all occurrences of devIdx
    unset($devs[$item]);
}
$devList = implode(",", $devs);
$query = "UPDATE Groups SET devIdxList=\"".$devList."\" WHERE userName=\"".$groupName."\"";
echo $query, "<br>";
$count = $db->exec($query);
if ($count == 1) {
    echo "<meta http-equiv=\"refresh\" content=\"1;url=/UpdateGroup.php/?groupName=",$groupName,"\"/>";
    echo "New device added to ",$groupName,"<br>";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
echo "<a href='/UpdateGroup.php/?groupName=",$groupName,"'>Show Group</a>";
?>
