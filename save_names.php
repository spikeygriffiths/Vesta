<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$numNames=$_POST["numNames"];
$handle = fopen("/home/pi/hubapp/usernames.txt", "w");
if ($handle) {
    for ($index = 0; $index < $numNames; $index++) {
        $name = "username".$index;
        $nameLine = $_POST[$name];
        $nameLine = $nameLine."\n";
        fputs($handle, $nameLine);
    }
    fclose($handle);
    // Should probably go through the rules and make sure the names are consistent
    echo "<meta http-equiv=\"refresh\" content=\"1;url=devices.php\" />";
    echo "New names saved";
} else {
    echo "<br>Try chmod 666 home/pi/hubapp/usernames.txt...<br>";
}
?>
