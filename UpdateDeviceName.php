<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$devIdx=$_GET['devIdx'];
$newUserName = $_POST["UserName"];  // Get new user name from form
echo "New name is:", $newUserName, " for device Id:",$devIdx, "<br>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
$oldUserName = DevGetItem("userName", $devIdx,$db);
$query = "UPDATE Devices SET userName=\"".$newUserName."\" WHERE devIdx=".$devIdx;
echo "About to send ",$query, " to DB<br>";
$count = $db->exec($query);
if ($count == 1) {
    UpdateRules($oldUserName, $newUserName);    // Now go through the rules and make sure the old name is updated to the new
    echo "<meta http-equiv=\"refresh\" content=\"0;url=/ShowOneDevice.php/?devIdx=",$devIdx,"\"/>";
    echo "New name saved";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
echo "<a href=/ShowOneDevice.php/?devIdx=",$devIdx,">Show Device</a>";

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

function UpdateRules($oldUserName, $newUserName)
{
    //echo "Replacing ",$oldUserName," with ",$newUserName;
    $inHandle = fopen("/home/pi/hubapp/rules.txt", "r");
    $outHandle = fopen("/home/pi/hubapp/new_rules.txt", "w");
    if ($inHandle && $outHandle) {
        while (!feof($inHandle)) {
            $line = fgets($inHandle);
            //echo "Read ",$line,"<br>";
            $newLine = str_replace($oldUserName, $newUserName, $line); // Replace old with new name
            //echo "Writing ",$newLine,"<br>";
            fputs($outHandle, $newLine);
        }
    }
    fclose($outHandle); 
    fclose($inHandle); 
    shell_exec("mv /home/pi/hubapp/rules.txt /home/pi/hubapp/old_rules.txt");
    shell_exec("mv /home/pi/hubapp/new_rules.txt /home/pi/hubapp/rules.txt");
    //shell_exec("chmod 666 /home/pi/hubapp/rules.txt");
}
?>
