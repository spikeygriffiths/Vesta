<?php
include "database.php";
error_reporting(E_ALL); 
$item = $_GET['item'];

echo "<html><body>";
echo "<center>";
if ($item == "All") {
    echo "<H1>All Rules</H1>";
} else {
    echo "<H1>Rules for ",$item,"</H1>";
}
$db = DatabaseInit();
ShowRules($db, $item);
echo "<p><center><a href=\"/index.php\">Home</a></center>";
echo "</body></html>";

function ShowRules($db, $item)
{
    $ruleTxts = [];
    $ruleIds = [];
    $index = 0;
    if ($item == "All") {
        $sth = $db->prepare("SELECT rowid, * FROM Rules");
    } else {
        $sth = $db->prepare("SELECT rowid, * FROM Rules WHERE rule LIKE '%".$item."%' ");
    }
    $sth->execute();
    while ($row =  $sth->fetch()) {
        $ruleTxts[$index] = $row['rule'];
        $ruleIds[$index] = $row['rowid'];
        $index++;
    }
    for ($ruleIdx = 0; $ruleIdx < $index/*sizeof(ruleTxts)?*/; $ruleIdx++) {
        echo "<form action=\"/save_rules.php/?ruleId=", $ruleIds[$ruleIdx], "&item=", $item, "\" method=\"post\">";
        echo "<input type=\"text\" size=\"100\" name=\"ruleTxt\" value=\"", $ruleTxts[$ruleIdx], "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
    }
    echo "<form action=\"/save_rules.php/?ruleId=-1&item=", $item, "\" method=\"post\">"; # Use -1 to indicate new rule
    echo "<input type=\"text\" size=\"100\" name=\"ruleTxt\" value=\"\"\">";
    echo "<input type=\"submit\" value=\"Update\"></form>";
}
?>
