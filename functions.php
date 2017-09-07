<?php
// functions.php
include "AppCmd.php";

function ElapsedTime($timeStamp)    // Creates a string describing age of $timeStamp
{
    $now = date('Y-m-d H:i:s');
    $elapsedSecs = abs(strtotime($now) - strtotime($timeStamp));
    $elapsedMins = floor($elapsedSecs / 60);
    $elapsedHours = floor($elapsedMins / 60);
    $elapsedDays = floor($elapsedHours / 24);
    if ($elapsedSecs < 120) return $elapsedSecs . " secs";
    if ($elapsedMins < 120) return $elapsedMins . " mins";
    if ($elapsedHours < 48) return $elapsedHours . " hours";
    return $elapsedDays . " days";
}

function GetVarVal($varName)
{
    $varsArray = [];
    $varsList = AppCmd("vars", True);
    $varsArray = explode(",", $varsList);
    $varVal = "Unknown";
    for ($index = 0; $index < count($varsArray); $index += 2) { // Search for variable name
        if ($varsArray[$index] == $varName) {
            $varVal = $varsArray[$index+1];
            break;
        }
    }
    return $varVal;
}

function SetVarVal($varName, $varVal)
{
    AppCmd("set " + $varName + " " + $varVal, False);
}
?>
