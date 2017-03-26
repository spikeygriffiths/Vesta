<?php

echo "<center>";
echo "<H1>Rules</H1>";
echo "</center>";
echo "<form action=\"save_rules.php\" method=\"post\">";
ShowRules("/home/pi/hubapp/rules.txt");
echo "<input type=\"submit\" value=\"Update Rules\">";
echo "</form>";
echo "<center>";
echo "<a href=\"index.php\">Home</a>";
echo "</center>";

function ShowRules($filename)
{
    $index = 0;
    $handle = fopen($filename, "r");
    if ($handle) {
        while (!feof($handle)) {
            $line = fgets($handle);
            echo "<input type=\"text\" size=\"100\" name=\"rule", $index, "\" value=\"", $line, "\"><br>";
            $index++;
        }
        fclose($handle); 
    }
    echo "<input type=\"text\" size=\"100\" name=\"rule", $index, "\"><br>"; // Always have a blank rule at the end to add 
    echo "<input type=\"hidden\" name=\"numRules\", value=\"",$index+1,"\">";
}
?>
