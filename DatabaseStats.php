<?php
include "database.php";
include "functions.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</style></head>";
echo "<body>";
PageHeader("Database Stats");
$db = DatabaseInit();
ShowAllStats($db);
echo "<br>";
PageFooter();
echo "</body></html>";

function ShowAllStats($db)
{
    #ShowStat($db, "Devices");
    #ShowStat($db, "Groups");
    #ShowStat($db, "Rules");
    echo "Database file on disk: ",GetDbFileSize()," bytes<br>";
    ShowStat($db, "Presence");
    ShowStat($db, "TemperatureCelsius");
    ShowStat($db, "SignalPercentage");
    ShowStat($db, "BatteryPercentage");
    ShowStat($db, "PowerReadingW");
    ShowStat($db, "EnergyConsumedWh");
    ShowStat($db, "EnergyGeneratedWh");
}

function ShowStat($db, $table)
{
    echo "Number of entries in ",$table," table = ",GetCount($db, $table),"<br>";
}

?>
