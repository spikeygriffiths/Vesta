<?php 
error_reporting(E_ALL); 

echo "<html><body>";
echo "<center><h1>Activity</h1> ";
echo "</center>";
ShowActivity("/home/pi/hubapp/activity.log");
echo "</form>";
echo "<center>";
echo "Click <a href=\"index.php\">here</a> to return";
echo "</center>";
echo "</body></html>";

function ShowActivity($names)
{
    $index = 0;
    $handle = fopen($names, "r");
    if ($handle) {
        while (!feof($handle)) {
            $line = fgets($handle);
            if ($line != "") {
                echo $line."<br>";
            }
        }
        fclose($handle); 
    } else echo "No activity!<br>"; // Else error opening file
}

?>
