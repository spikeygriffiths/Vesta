<?php
error_reporting(E_ALL);
$devKey=$_GET['devKey'];
$type=$_POST["type"];
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/Schedule.php/?devKey=",$devKey,"&type=",$type,"\"/>";
?>
