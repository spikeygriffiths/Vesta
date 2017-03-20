<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$devIdx=$_GET['devIdx'];
$name = $_POST["UserName"];  // Get new user name from form
echo "New name is:", $name, " for device Id:",$devIdx, "<br>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_WARNING);
$query = "UPDATE Devices SET userName=\"".$name."\" WHERE devIdx=".$devIdx;
echo "About to send ",$query, " to DB<br>";
$count = $db->exec($query);
if ($count == 1) {
    // Should probably go through the rules and make sure the names are consistent.  Need old name as well as new one...
    echo "<meta http-equiv=\"refresh\" content=\"1;url=/ShowOneDevice.php/?devIdx=",$devIdx,"\"/>";
    echo "New name saved";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
?>
