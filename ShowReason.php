<?php
include "database.php";
include "functions.php";
$event = $_GET['event'];
$reason = $_GET['reason'];
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
PageHeader("Reason for ".$event);
$db = DatabaseInit();
echo "<center>";
if (substr($reason, 0, 5) == "Rule:") {
    $ruleId = substr($reason, 5);
    ShowRule($db, $ruleId);
} else {
    echo "Reason is ",$reason,"<br>";
}
PageFooter();
echo "</body></html>";

function ShowRule($db, $ruleId)
{
    $sth = $db->prepare("SELECT rowid, * FROM Rules WHERE rowid=".$ruleId);
    $sth->execute();
    $row =  $sth->fetch();
    $ruleTxt = $row['rule'];
    echo "<form action=\"/vesta/save_rules.php/?ruleId=", $ruleId, "&item=", $item, "\" method=\"post\">";
    echo "<input type=\"text\" size=\"100\" name=\"ruleTxt\" value=\"", $ruleTxt, "\">";
    echo "<input type=\"submit\" value=\"Update\"></form>";
}
?>
