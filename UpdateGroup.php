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
echo "<center><h1>",$groupName,"</h1>";
echo "<button type=\"button\" onclick=\"window.location.href='/DelGroup.php/?groupName=",$groupName,"'\">Remove all of ",$groupName,"</button><br><br>";
ShowGroupInfo($db, $groupName);
echo "<a href=\"/Groups.php\">Groups</a><br>";
echo "<br><a href=\"/index.php\">Home</a> </center>";
echo "</body></html>";

function  DbGetItem($item, $devKey, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devKey=".$devKey);
    $result->setFetchMode(PDO::FETCH_ASSOC);
    $fetch = $result->fetch();
    return $fetch[$item];
}

function ShowGroupInfo($db, $groupName)
{
    echo "<table>";
    echo "<form action=\"/UpdateGroupName.php/?oldName=",$groupName,"\" method=\"post\">";
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
                $devName = DbGetItem("userName", $devKey, $db);
                echo"<tr><td> ".$devName." </td><td><a href='/DelDevFromGroup.php/?groupName=",$groupName,"&devKey=",$devKey,"'>Delete</a></td></tr>";
            }
        } else {
            echo"<tr><td><i>null</i></td><td></td></tr>";
        }
    } else {
        echo"<tr><td><i>empty</i></td><td></td></tr>";
    }
    echo "</table>";
    echo "<form action='/AddDevToGroup.php/?groupName=",$groupName,"' method='post'>";
    echo "<p>Add device<select id='devKey' name='devKey'>";
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    $numDevs = $result->fetchColumn();
    for ($idx=0; $idx<$numDevs; $idx++) {
        $userName = DbGetItem("userName", $idx, $db);
        echo "<option value='",$idx,"'>",$userName,"</option>";
    }
    echo "</select><p>";
    echo "<input type='submit'/>";
    echo "</form>";
}
?>
