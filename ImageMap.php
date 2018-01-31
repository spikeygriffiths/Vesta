<?php
// ImageMap.php
// Gets X and Y from mouse click pos as well as command & deviceId from URL
error_reporting(E_ALL);
include "AppCmd.php";
$cmd = $_GET['cmd'];
$devId = $_GET['devId'];
$map = $_GET['map'];
$map = substr($map, 1);   // Remove leading "?" prepended by ismap
echo "cmd:",$cmd,"<br>devId=",$devId,"<br>map=",$map,"<br>";
$coords = explode(",", $map);
$x = $coords[0];
$y = $coords[1];
if (($cmd == "hue") || ($cmd == "sat") || ($cmd == "dim")) {
    $cmd = $cmd." ".$devId." ".$x;  // Just use X for these commands
    echo "Command=",$cmd,"<br>";
    AppCmd($cmd, false);
}
echo "Came from:",$_SERVER['HTTP_REFERER'],"<br>";
header('location:'.$_SERVER['HTTP_REFERER']);
?>

