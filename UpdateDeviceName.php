<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$devIdx=$_GET['devIdx'];
$name = $_POST["UserName"];  // Get new user name from form
echo "New name is:", $name, " for device Id:",$devIdx;
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$db->exec("UPDATE Devices SET UserName=\"".$name."\" WHERE devRowId=".$devIdx);
// Should probably go through the rules and make sure the names are consistent.  Need old name as well as new one...
echo "<meta http-equiv=\"refresh\" content=\"1;url=/ShowOneDevice.php/?devIdx=",$devIdx,"\"/>";
echo "New name saved";
?>
