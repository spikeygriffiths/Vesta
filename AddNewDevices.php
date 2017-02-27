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
echo "<form action=\"save_names.php\" method=\"post\">";
ShowNewDevices("/home/pi/hubapp/usernames.txt");
echo "<input type=\"submit\" value=\"Update Names\">";
echo "</form>";
echo "<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>";
echo "<center>";
echo "Click <a href=\"index.php\">here</a> to return";
echo "</center>";
echo "</body>";
echo "</html>";

function ShowNewDevices($names)
{
    $index = 0;
    $handle = fopen($names, "r");
    if ($handle) {
        echo "<table>";
        while (!feof($handle)) {
            $line = fgets($handle);
            if ($line != "") {
                if (substr($line, 0, 5)=="(New)") {
                    $username = "username".$index;
                    echo "<tr><td><input type=\"size\" text=\"20\" name=\"",$username, "\" value=\"", $line, "\"></td>";
                }
            }
        }
        fclose($handle); 
        echo "</table>";
    } else echo "No devices!<br>"; // Else error opening file
    echo "<input type=\"hidden\" name=\"numNames\", value=\"",$index,"\">";
}
?>
