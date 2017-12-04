<?php 
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
PageHeader("Groups");
$db = DatabaseInit();
ShowGroups($db);
echo "<br>";
PageFooter();
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
        echo "<tr><td><a href=\"/vesta/UpdateGroup.php/?groupName=",$groupName,"\">",$groupName,"</a></td>";
        echo"<td> ".$devs." </td></tr>";
    }
    echo"<tr><td> <a href=\"/vesta/UpdateGroup.php/?groupName=NewGroup\"><i>New Group</i></a> </td><td> <i>empty</i> </td></tr>";
    echo "</table>";
}

?>
