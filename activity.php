<?php 
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
echo "<center><h1>Activity</h1> </center>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
ShowActivity($db);
echo "<center><a href=\"index.php\">Home</a></center>";
echo "</body></html>";

function  DbGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowActivity($db)
{
    $sth = $db->prepare("SELECT * FROM Events");
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $username = DbGetItem("userName", $row['devIdx'],$db);        // Use $row['devIdx'] as key into Devices table to get $userName
        echo"<tr><td>".$username."</td><td>".$row['timestamp']."</td><td>".$row['item']."</td><td>".$row['value']."</td></tr>";
    }
    echo "</table>";
}

?>
