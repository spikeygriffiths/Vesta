<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$result = $db->query("SELECT COUNT(*) FROM Devices");
$numDevs = $result->fetchColumn();
for ($devIndex = 0; $devIndex < $numDevs; $devIndex++) {
    $name = "UserName".$index;
    $nameLine = $_POST[$name];
    $db->exec("UPDATE Devices SET Username=\""+$name+"\" WHERE rowid=".str($devIndex));
}
// Should probably go through the rules and make sure the names are consistent.  Need old name as well as new one...
echo "<meta http-equiv=\"refresh\" content=\"1;url=devices.php\" />";
echo "New names saved";
?>
