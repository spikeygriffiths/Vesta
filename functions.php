<?php
// functions.php
include "AppCmd.php";   # Not allowed to include same file more than once, so if including this "functions.php", must remove any previous include "AppCmd.php"

function PageHeader($title, $right = Null)
{
    echo "<center>";
    echo "<div class=\"pageHead\">";
    echo "<div class=\"pageButton\"><a href=\"/vesta/index.php\"><img src=\"/vesta/vestaLogo.png\" width=32 height=32 title=\"Home\"></a></div>";
    echo "<div class=\"pageTitle\">",$title,"</div>";
    if ($right != Null) {
        echo "<div class=\"pageButton\">",$right,"</div>";
    } else {    // No right button supplied
        echo "<div class=\"pageEmpty\">&nbsp;</div>";
    }
    echo "</div>";
}

function PageFooter()
{
    echo "<center><a href=\"/vesta/index.php\"><img src=\"/vesta/vestaLogo.png\" width=32 height=32 title=\"Home\"></a>";
    //echo "<button class=\"buttonHome\" type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
}

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
