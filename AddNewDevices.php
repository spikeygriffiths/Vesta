<?php
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
echo "<html>";
echo "<head><script src=\"https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js\"></script>";
echo "<script type=\"text/javascript\">";
echo "function HubCmd(addr)";
echo "{ $.ajax( {type : 'POST', data : { }, url : addr, success: function(data) { ";
//echo "if (data!='') { ";
echo "    $('body').append(data);";  // Only works reliably from button press, not from timer
echo "alert(data);";
//echo " }";
echo " }, error: function(xhr) { alert(\"error!\"); } }); }";
echo "$(document).ready(function() { setInterval(\"HubCmd('open.php')\", 10000); });";
echo "</script>";
echo "</head>";
echo "<body>";
echo "<center><h1>Add New Devices</h1> ";
echo "Now: ", date('Y-m-d H:i:s'), "<br><br>"; // Show page refreshing
echo "<button type=\"button\" onclick=\"HubCmd('open.php')\">Open hub for 1 minute</button><br>";
echo "</center>";
echo "<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>";
echo "<center>";
echo "Click <a href=\"index.php\">here</a> to return";
echo "</center>";
echo "</body>";
echo "</html>";
?>
