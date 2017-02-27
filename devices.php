<?php 
error_reporting(E_ALL); 

echo "<html><head>";
echo "<style>table {";
echo "font-family:arial, sans-serif;";
echo "border-collapse: collapse;";
echo "width: 100 % }";
echo "td, th {";
echo "border: 2px solid #dddddd;";
echo "text-align: left;";
echo "padding: 2px }";
echo "tr:nth-child(even) { background-color: #dddddd; }";
echo "</style>";
echo "</head><body>";
echo "<center><h1>Devices</h1> ";
echo "<button type=\"button\" onclick=\"window.location.href='AddNewDevices.php'\">Add new devices</button><br>";
echo "</center>";
echo "<form action=\"save_names.php\" method=\"post\">";
ShowDevices("/home/pi/hubapp/usernames.txt", "/home/pi/hubapp/status.xml");
echo "<input type=\"submit\" value=\"Update Names\">";
echo "</form>";
echo "<center>";
echo "Click <a href=\"index.php\">here</a> to return";
echo "</center>";
echo "</body></html>";

function ShowDevices($names, $status)
{
    $index = 0;
    $handle = fopen($names, "r");
    if (file_exists($status)) {
        $xml = simplexml_load_file($status) or die("Can't open ".$status);
    } else die("Can't find ".$status);
    if ($handle) {
        echo "<table>";
        echo "<tr><th>Name</th><th>Battery %</th><th>Temperature (C)</th><th>Presence</th><th>Notes</th></tr>";
        while (!feof($handle)) {
            $line = fgets($handle);
            if ($line != "") {
                echo "<tr><td><input type=\"size\" text=\"20\" name=\"index", $username, "\" value=\"", $line, "\"></td>";
                $battLvl = $xml->device[$index]->Battery;
                if ("N/A" != $battLvl) {
                    echo "<td>".$battLvl."%</td>";
                } else {
                    echo "<td>".$battLvl."</td>";
                }
                $temp = $xml->device[$index]->Temperature;
                if ("N/A" != $temp) {
                    echo "<td>".$temp."'C</td>";
                } else {
                    echo "<td>".$temp."</td>";
                }
                echo "<td>".$xml->device[$index]->Presence."</td>";
                echo "<td>".$xml->device[$index]->Other."</td></tr>";
                $index++;
            }
        }
        echo "</table>";
        fclose($handle); 
    } else echo "No devices!<br>"; // Else error opening file
    echo "<input type=\"hidden\" name=\"numNames\", value=\"",$index,"\">";
}

?>
