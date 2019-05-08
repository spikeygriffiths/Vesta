<?php
$url1 = $_SERVER['REQUEST_URI'];
header("Refresh: 10;  URL=$url1");
include "functions.php";
include "database.php";
error_reporting(E_ALL);
echo "<html><head>";    // NB This header file also starts the html head tag (but doesn't end it, to allow pages to extend the head)
echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">";  # So it works on mobile phones as well as laptops
echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"/vesta/vesta.css\">";
echo "</head><body>";
$db = DatabaseInit();
echo "<title>","Vesta Panel","</title>"; # For browser tab
echo "<center>";
$title = "<img src='vestaTitle.png' title=\"Vesta was the Roman goddess of hearth and home\" width=64 height=64>";
echo $title."<br>"; //PageHeader($title, $rightBtn);
$ps = shell_exec("ps ax");
$appRunning = (strpos($ps, "vesta.py") !== false);
//echo "Current PHP version: ".phpversion()."<br>";
echo "<H4>".date("l j F ")."</H4><H1>".TimeInWords()."</H1>";
$forecast = GetForecast($db);
echo $forecast."<br>";
$statusPage = "status.html";
$boiler = "BoilerController";
$clamp = "PowerClamp";
if ($appRunning) {
    //echo "UpTime: ",AppCmd("uptime", True),"<br>";
    $housePower = GetDevStatus("PowerReadingW", $clamp, $db);
    echo "<H2>",$housePower,"W</H2>";
    //$houseTemp = GetDevStatus("SourceCelsius", $boiler, $db);
    //$targetTemp = GetDevStatus("TargetCelsius", $boiler, $db);
    //echo "<H4>House:",$houseTemp,"'C, Target:",$targetTemp,"'C</H4><br>";
    $boostDegC = GetConfig("BoostDegC", "21", $db);
    $frostDegC = GetConfig("FrostDegC", "7", $db);
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setTargetTemp ",$boiler," ",$boostDegC," 3600'\">Boost</button>&nbsp&nbsp&nbsp&nbsp&nbsp";
    echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/Command.php/?cmd=setTargetTemp ",$boiler," ",$frostDegC," 3600'\">Frost</button><br><br>";
    //echo "<button class=\"button\" type=\"button\" onclick=\"window.location.href='/vesta/RequestStatus.php'\">Status</button>";
    echo "</center>";
 } else {
    echo "<br>";
    echo "<center><h2>Vesta app stopped</h2></center>"; 
    echo "<br><br><button type=\"button\" onclick=\"window.location.href='/vesta/restart.php'\">Restart</button><br><br>";
}
echo "</body></html>";

function GetForecast($db)
{
    $apiKey = GetConfig("owmApiKey", "", $db);
    $cityId = GetConfig("owmLocation", "", $db);
    $apiUrl = "http://api.openweathermap.org/data/2.5/weather?q=".$cityId."&lang=en&units=metric&APPID=".$apiKey;
    $ch = curl_init(); // Requires apt-get install curl
    curl_setopt($ch, CURLOPT_HEADER, 0);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_VERBOSE, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    $response = curl_exec($ch);
    curl_close($ch);
    $data = json_decode($response);
    //echo $response."<br>";
    return $data->weather[0]->description;
    //echo <img src="http://openweathermap.org/img/w/<?php echo $data->weather[0]->icon; ?>.png>"
    //echo $data->main->temp_max;
    //echo $data->main->temp_min;
}

function TimeInWords()
{
    $list1 = array('', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve');
    $hours = date("g");
    $minutes = date("i");
    if ($minutes >= 33) $hours = $hours + 1; // For "Quarter to ..."
    if ($hours > 12) $hours = 1;
    $hourTxt = $list1[$hours];
    if (($minutes > 58) || ($minutes < 3)) {
        return $hourTxt." o'clock";
    } elseif ($minutes < 8) {
        return "Five past ".$hourTxt;
    } elseif ($minutes < 13) {
        return "Ten past ".$hourTxt;
    } elseif ($minutes < 18) {
        return "Quarter past ".$hourTxt;
    } elseif ($minutes < 23) {
        return "Twenty past ".$hourTxt;
    } elseif ($minutes < 28) {
        return "Twenty Five past ".$hourTxt;
    } elseif ($minutes < 33) {
        return "Half past ".$hourTxt;
    } elseif ($minutes < 38) {
        return "Twenty Five to ".$hourTxt;
    } elseif ($minutes < 43) {
        return "Twenty to ".$hourTxt;
    } elseif ($minutes < 48) {
        return "Quarter to ".$hourTxt;
    } elseif ($minutes < 53) {
        return "Ten to ".$hourTxt;
    } elseif ($minutes < 58) {
        return "Five to ".$hourTxt;
    }
    return $hours.":".$minutes;
}

function GetDevStatus($item, $devName, $db)
{
    $devKey = GetDevKeyFromItem("UserName", $devName, $db);
    if ($devKey != null) {
        $row = GetLatestLoggedItem($item, $devKey, $db);
        if ($row != null) {
            return $row['value'];
        }
        return "N/A (".$devKey.")";
    }
    return "No such device";
}

?>
