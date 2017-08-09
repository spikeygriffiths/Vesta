<?php 
include "database.php";
error_reporting(E_ALL); 

echo "<html>";
echo "<head><style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style></head>";
echo "<body>";
echo "<center><h1>Groups</h1>";
$db = DatabaseInit();
ShowGroups($db);
echo "<br>";
echo "<button type=\"button\" onclick=\"window.location.href='/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowGroups($db)
{
    $sth = $db->prepare("SELECT * FROM Groups");
    $sth->execute();
    echo "<table>";
    while ($row =  $sth->fetch()) {
        $groupName = $row['userName'];
        $devList = $row['devKeyList'];
        if ($devList != "") {
            $devArray = explode(",", $devList);
            $devs = "";
            for ($index = 0; $index < count($devArray); $index++) {
                $devKey = $devArray[$index];
                $devName = GetDevItem("userName", $devKey, $db);
                if ($devs != "") {
                    $devs .= ", ";
                }
                $devs .= $devName;
            }
        } else {
            $devs = "<i>empty</i>";
        }
        echo "<tr><td><a href=\"/UpdateGroup.php/?groupName=",$groupName,"\">",$groupName,"</a></td>";
        echo"<td> ".$devs." </td></tr>";
    }
    echo"<tr><td> <a href=\"/UpdateGroup.php/?groupName=NewGroup\"><i>New Group</i></a> </td><td> <i>empty</i> </td></tr>";
    echo "</table>";
}

?>
