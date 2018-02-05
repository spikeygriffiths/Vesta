<?php
include "database.php";
include "functions.php";
$item = $_GET['item'];
$type = $_GET['type'];
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
echo "<center>";
PageHeader("Configuration");
$db = DatabaseInit();
ShowConfig($db);
PageFooter();
echo "</body></html>";

function ShowConfig($db)
{
    $rowIds = [];
    $items = [];
    $values = [];
    $index = 0;
    $sth = $db->prepare("SELECT rowid, * FROM Config");
    $sth->execute();
    while ($row =  $sth->fetch()) {
        $rowIds[$index] = $row['rowid'];
        $items[$index] = $row['item'];
        $values[$index] = $row['value'];
        $index++;
    }
    for ($confIdx = 0; $confIdx < $index; $confIdx++) {
        echo $items[$confIdx];
        echo "<form action=\"/vesta/save_config.php/?item=", $items[$confIdx], "&value=", $value, "\" method=\"post\">";
        echo "<input type=\"text\" size=\"100\" name=\"valueTxt\" value=\"", $values[$confIdx], "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
    }
}
?>
