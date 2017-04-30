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

?>
