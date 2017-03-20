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
ShowNewDevices();
echo "<br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>";
echo "<center><a href=\"index.php\">Home</a></center>";
echo "</body>";
echo "</html>";

function ShowNewDevices()
{
    $dir = "sqlite:/home/pi/hubapp/hubstuff.db";
    $db = new PDO($dir) or die("Cannot open database");
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    $numDevs = $result->fetchColumn();
    echo "<table>";
    echo "<tr><th>Name</th><th>Type</th></tr>";
    for ($devIdx = 0; $devIdx < $numDevs; $devIdx++) {
        $result = $db->query("SELECT userName, modelName FROM devices WHERE devIdx=".$devIdx);
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        $username = $fetch[UserName];
        $modelname = $fetch[ModelName];
        //if (substr($username, 0, 5)=="(New)") {
            echo "<tr><td>",$username,"</td><td>",$modelname,"</td></tr>";
        //}
        echo "</table>";
    }
}
?>
