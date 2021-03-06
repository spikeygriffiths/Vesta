<?php
include "database.php";
include "functions.php";
$item = $_GET['item'];
if (isset($_GET['type'])) {
    $type = $_GET['type'];
} else $type = "";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
if ($item == "All") {
    PageHeader("All Rules");
} else {
    PageHeader("Rules for ".$item);
}
$db = DatabaseInit();
echo "<center>";
ShowRules($db, $item);
if ($item != "All") {
    if ($type == "dev") {
        $devKey = $_GET['devKey'];
        echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/ShowOneDevice.php/?devKey=",$devKey,"'\">",$item,"</button><br><br>";
    } else if ($type == "vars") {
        echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Variables.php'\">Variables</button><br><br>";
    }
}
PageFooter();
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
    for ($ruleIdx = 0; $ruleIdx < $index; $ruleIdx++) {
        echo "<form action=\"/vesta/save_rules.php/?ruleId=", $ruleIds[$ruleIdx], "&item=", $item, "\" method=\"post\">";
        echo "<input type=\"text\" size=\"100\" name=\"ruleTxt\" value=\"", $ruleTxts[$ruleIdx], "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
    }
    echo "<form action=\"/vesta/save_rules.php/?ruleId=-1&item=", $item, "\" method=\"post\">"; # Use -1 to indicate new rule
    echo "<input type=\"text\" size=\"100\" name=\"ruleTxt\" value=\"\"\">";
    echo "<input type=\"submit\" value=\"Update\"></form>";
}
?>
