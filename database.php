<?php
// database.php

function DatabaseInit()
{
    $dir = "sqlite:/home/pi/hubapp/hubstuff.db";
    $db = new PDO($dir) or die("Cannot open database");
    return $db;
}

function GetDevCount($db)
{
    $result = $db->query("SELECT COUNT(*) FROM Devices");
    return $result->fetchColumn();
}

function GetDevKey($index, $db)
{
    $item = "devKey";
    $result = $db->query("SELECT ".$item." from Devices LIMIT 1 OFFSET ".$index);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function GetDevItem($item, $devKey, $db)
{
    $result = $db->query("SELECT ".$item." FROM Devices WHERE devKey=".$devKey);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function  GetDevStatus($item, $devKey, $db)
{
    $result = $db->query("SELECT ".$item." FROM Status WHERE devKey=".$devKey);
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch[$item];
        }
    }
    return null;
}

function UpdateRules($oldUserName, $newUserName, $db)
{
    $updates = [];    # Get ready to make a list of all the updates
    $numRules = 0;
    $query = "SELECT rowid, * FROM Rules WHERE rule LIKE '%".$oldUserName."%' "; # Get all rules that mention our old device name
    echo "Checking rules using ", $query, "<br>";
    $sth = $db->prepare($query);
    $sth->execute();
    while ($row =  $sth->fetch()) {
        $ruleTxt = $row['rule'];
        $ruleId = $row['rowid'];
        echo "Here's a rule that mentions ",$oldUserName, " - ", $ruleTxt, "<br>";
        $newRule = str_replace($oldUserName, $newUserName, $ruleTxt); // Replace old with new name
        echo "Updated rule that mentions ",$oldUserName, " - ", $newRule, "<br>";
        $updates[$numRules++] = "UPDATE Rules SET rule=\"".$newRule."\" WHERE rowid=".$ruleId; # Build query to update existing rule
    }
    for ($index = 0; $index < $numRules; $index++) {
        $count = $db->exec($updates[$index]); # Run all the updates
    }
}

function GetAppState($item, $db)
{
    $result = $db->query("SELECT Value FROM AppState WHERE Name=\"".$item."\"");
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch["Value"];
        }
    }
    return null;
}

function SetAppState($item, $val, $db)
{
    $db->exec("REPLACE INTO AppState VALUES(\"".$item."\", \"".$val."\")"); # Run the update
}

?>
