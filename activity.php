<?php 
error_reporting(E_ALL); 

echo "<html><body>";
echo "<center><h1>Activity</h1> </center>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
ShowActivity($db);
echo "<center><a href=\"index.php\">Home</a></center>";
echo "</body></html>";

function ShowActivity($db)
{
    $sth = $db->prepare("SELECT * FROM Events");
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        // Use $row['devIdx'] as key into Devices table to get $userName
        echo"<tr><td>".$row['timestamp']."</td><td>".$row['item']."</td><td>".$row['value']."</td></tr>";
    }
    echo "</table>";
}

?>
