<?php
error_reporting(E_ALL); 
include "HubCmd.php";

$cmd = $_GET['cmd'];
$expRsp = false;    
HubCmd($cmd, $expRsp);

header('location:.' . $_SERVER['HTTP_REFERER']);
?>

