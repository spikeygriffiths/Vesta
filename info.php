<?php 
error_reporting(E_ALL); 
include "HubCmd.php";

echo "<html><head>";
echo "</head><body>";
echo "<center><h1>Info Command</h1></center>";
echo nl2br(HubCmd("info", True));
echo "</body>";
?>
