<?php
error_reporting(E_ALL); 
include "HubCmd.php";

ini_set('display_errors', '1');
$devId=$_GET['devId'];   // Get deviceId to delete from URL
$cmd= "removeDevice ".$devId;
HubCmd($cmd, false);

header('location:'.$_SERVER['HTTP_REFERER']);
?>
