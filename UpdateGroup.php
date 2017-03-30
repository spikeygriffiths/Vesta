<?php
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
$groupName=$_GET['groupName'];
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
echo "<center><h1>",$groupName,"</h1></center>";
ShowGroupInfo($db, $groupName);
echo "<center><a href=\"/Groups.php\">Groups</a> </center><br>";
echo "<center><a href=\"/index.php\">Home</a> </center>";
echo "</body></html>";

function  DevGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function ShowGroupInfo($db, $groupName)
{
    echo "<form action=\"/UpdateGroupName.php/?oldName=",$groupName,"\" method=\"post\">";
    echo "<table>";
    echo "<tr><td>Name</td><td><input type=\"text\" name=\"NewName\" value=\"", $groupName, "\"></td>";
    echo "</table>";
    echo "<input type=\"submit\" value=\"Submit\" name=\"Update name\"></form><br>";
}
?>
