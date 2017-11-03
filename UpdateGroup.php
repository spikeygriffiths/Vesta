<?php
include "database.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "<style>table {font-family:arial, sans-serif;border-collapse: collapse;width: 100 % }";
echo "td, th {border: 2px solid #dddddd;text-align: left;padding: 2px }";
echo "</style>";
echo "</head><body>";
$groupName=$_GET['groupName'];
$db = DatabaseInit();
echo "<center><h1>",$groupName,"</h1>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/DelGroup.php/?groupName=",$groupName,"'\">Remove all of ",$groupName,"</button><br><br>";
ShowGroupInfo($db, $groupName);
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/Groups.php'\">Groups</button><br><br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowGroupInfo($db, $groupName)
{
    echo "<table>";
    echo "<form action=\"/vesta/UpdateGroupName.php/?oldName=",$groupName,"\" method=\"post\">";
    echo "<tr><td><input type=\"text\" name=\"NewName\" value=\"", $groupName, "\"></td>";
    echo "<td><input type=\"submit\" value=\"Update name\"></form></td></tr>";
    $sth = $db->prepare("SELECT devKeyList FROM Groups WHERE userName=\"".$groupName."\"");
    $sth->execute();
    $sth->setFetchMode(PDO::FETCH_ASSOC);
    $row =  $sth->fetch();
    if ($row != null) {
        $devList = $row['devKeyList'];
        if ($devList != "") {
            $devArray = explode(",", $devList);
            for ($index = 0; $index < count($devArray); $index++) {
                $devKey = $devArray[$index];
                $devName = GetDevItem("userName", $devKey, $db);
                echo"<tr><td> ".$devName." </td><td><a href='/vesta/DelDevFromGroup.php/?groupName=",$groupName,"&devKey=",$devKey,"'>Delete</a></td></tr>";
            }
        } else {
            echo"<tr><td><i>null</i></td><td></td></tr>";
        }
    } else {
        echo"<tr><td><i>empty</i></td><td></td></tr>";
    }
    echo "</table>";
    echo "<form action='/vesta/AddDevToGroup.php/?groupName=",$groupName,"' method='post'>";
    echo "<p>Add device<select id='devKey' name='devKey'>";
    $numDevs = GetDevCount($db);
    for ($idx=0; $idx<$numDevs; $idx++) {
        $devKey = GetDevKey($idx, $db);
        $userName = GetDevItem("userName", $devKey, $db);
        echo "<option value='",$idx,"'>",$userName,"</option>";
    }
    echo "</select><p>";
    echo "<input type='submit'/>";
    echo "</form>";
}
?>
