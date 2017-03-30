<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$oldGroupName=$_GET['oldName'];
$newGroupName = $_POST["NewName"];  // Get new user name from form
echo "New name is:", $newGroupName, " to replace old name of:",$oldGroupName, "<br>";
$dir = "sqlite:/home/pi/hubapp/hubstuff.db";
$db = new PDO($dir) or die("Cannot open database");
if ($oldGroupName == "NewGroup") {
    $query = "INSERT INTO Groups (userName, devIdxList) VALUES (\"".$newGroupName."\",\"\")";  # Insert new name and empty string for devices
} else {
    $query = "UPDATE Groups SET userName=\"".$newGroupName."\" WHERE userName=\"".$oldGroupName."\"";
}
echo "About to send ",$query, " to DB<br>";
$count = $db->exec($query);
if ($count == 1) {
    UpdateRules($oldGroupName, $newGroupName);    // Now go through the rules and make sure the old name is updated to the new
    echo "<meta http-equiv=\"refresh\" content=\"10;url=/UpdateGroup.php/?groupName=",$newGroupName,"\"/>";
    echo "New name saved";
} else {
    echo "Update failed, with count of:", $count, "<br>";
}
echo "<a href=/UpdateGroup.php/?groupName=",$newGroupName,">Show Group</a>";

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
