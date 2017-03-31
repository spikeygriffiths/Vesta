<?php 
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
echo "<center><h1>Groups</h1>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
ShowGroups($db);
echo "<p><center><a href=\"/index.php\">Home</a></center>";
echo "</body></html>";

function  DbGetItem($item, $devIdx, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devIdx=".$devIdx);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowGroups($db)
{
    $sth = $db->prepare("SELECT * FROM Groups");
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $groupName = $row['userName'];
        $devList = $row['devIdxList'];
        if ($devList != "") {
            $devArray = explode(",", $devList);
            $devs = "";
            for ($index = 0; $index < count($devArray); $index++) {
                $devIdx = $devArray[$index];
                $devName = DbGetItem("userName", $devIdx, $db);
                if ($devs != "") {
                    $devs .= ", ";
                }
                $devs .= $devName;
            }
        } else {
            $devs = "<i>empty</i>";
        }
        echo "<tr><td><a href=\"UpdateGroup.php/?groupName=",$groupName,"\">",$groupName,"</a></td>";
        echo"<td> ".$devs." </td></tr>";
    }
    echo"<tr><td> <a href=\"UpdateGroup.php/?groupName=NewGroup\"><i>New Group</i></a> </td><td> <i>empty</i> </td></tr>";
    echo "</table>";
}

?>
