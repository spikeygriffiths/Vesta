<?php
session_start();
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
error_reporting(E_ALL); 
include "database.php";

echo "<html>";
echo "<head></head>";
echo "<body>";
echo "<center><h1>Users</h1>";
$db = DatabaseInit();
ShowUsers($db);
echo "<br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/AddNewUser.php'\">Add new user</button><br><br>";
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

function ShowUsers($db)
{
    $sth = $db->prepare("SELECT * FROM Users");
    $sth->execute();
    $index = 0;
    while ($row =  $sth->fetch()) {
        $names[$index] = $row['name'];
        $ids[$index] = $row['id'];
        $index++;
    }
    for ($userIdx = 0; $userIdx < $index; $userIdx++) {
        echo "<form action=\"/vesta/DeleteUser.php/?userId=", $ids[$userIdx], "\" method=\"post\">";
        echo "<input type=\"text\" size=\"100\" name=\"userName\" value=\"", $names[$userIdx], "\">";
        echo "<input type=\"submit\" value=\"Remove\"></form>";
    }
}
?>
