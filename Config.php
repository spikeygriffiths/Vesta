<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
PageHeader("Configuration");
$db = DatabaseInit();
ShowConfig($db);
PageFooter();
echo "</body></html>";

function ShowConfig($db)
{
    $sth = $db->prepare("SELECT * FROM Config");
    $sth->execute();
    echo "<div class=\"configForm\">";
    while ($row =  $sth->fetch()) {
        $item = $row['item'];
        $value = $row['value'];
        //echo "<form align=\"right\" action=\"/vesta/save_config.php/?item=", $item, "\" method=\"post\">",$item,": "; // I can't get form to be right-aligned inside <div> element
        echo "<form action=\"/vesta/save_config.php/?item=", $item, "\" method=\"post\">",$item,": ";
        echo "<input type=\"text\" size=\"50\" name=\"valueTxt\" value=\"", $value, "\">";
        echo "<input type=\"submit\" value=\"Update\"></form>";
    }
    echo "<form action=\"/vesta/save_config.php/?item=NewItem\" method=\"post\">New item: ";
    echo "<input type=\"text\" size=\"20\" name=\"valueTxt\" value=\"\"\>";
    echo "<input type=\"submit\" value=\"Update\"></form>";
    echo "</div>";
}
?>
