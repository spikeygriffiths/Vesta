<?php
error_reporting(E_ALL);
ini_set('display_errors', '1');
$numRules=$_POST["numRules"];
$handle = fopen("/home/pi/hubapp/rules.txt", "w");
if ($handle) {
    $previousRule = "";
    for ($index = 0; $index < $numRules; $index++) {
        $name = "rule".$index;
        $ruleLine = $_POST[$name];
        $ignore = False;
        if ($ruleLine == "") {
            if ($previousRule == "") { // Lose any double blank lines
                $ignore = True;
            }
        }
       $previousRule = $ruleLine;
        if ($ignore == False) {
            $ruleLine = $ruleLine."\n";
            fputs($handle, $ruleLine);
        }
    }
    fclose($handle); 
    echo "<meta http-equiv=\"refresh\" content=\"1;url=rules.php\" />";
    echo "New rules saved";
} else {
    echo "<br>Try chmod 666 home/pi/hubapp/rules.txt...<br>";
}
?>
