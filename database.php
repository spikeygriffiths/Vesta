<?php
// database.php
session_start();

function DatabaseInit()
{
    $dir = "sqlite:/home/pi/Vesta/vesta.db";
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

function  GetDevStatusAtTime($item, $devKey, $db, $time)
{
    $result = $db->query("SELECT ".$item." FROM Status WHERE devKey=".$devKey." AND ".$item."_time > ".$time);
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

function CreateUser($name, $email, $passwordHash, $db)
{
    $query = 'SELECT * FROM Users WHERE name = "'.$name.'" OR email = "'.$email.'"';  // Check that name or email doesn't already exist
    $sth = $db->prepare($query);
    $sth->execute();
    $row = $sth->fetch();
    if ($row == null) {
        $insert = 'INSERT INTO Users (name, passwordHash, email) VALUES("'.$name.'", "'.$passwordHash.'", "'.$email.'")';
        $db->exec($insert);   # Add the new user
        return "New user ".$name." now added";  // Success
    } return "Sorry, that username / email is already taken. Please choose another one.";
}

function GetNumUsers($db)
{
    $result = $db->query("SELECT COUNT(*) FROM Users");
    return $result->fetchColumn();
}

function NewEvent($devKey, $event, $db) # $devKey is the deviceId. Use 0 for hub
{
    $insert = 'INSERT INTO Events (timestamp, event, devKey) VALUES("'.date('Y-m-d H:i:s').'", "'.$event.'", '.$devKey.')';  # Insert event with local timestamp
    $db->exec($insert);   # Add the new event
}

function CheckPasswordCorrectnessAndLogin($name, $password, $db)
{
    $query = 'SELECT name, email, passwordHash FROM Users WHERE name = "'.$name.'" OR email = "'.$name.'" LIMIT 1'; // Allow the user to log in with username or email address
    $sth = $db->prepare($query);
    $sth->execute();
    $row = $sth->fetch();
    if ($row) {
        $passwordHash = password_hash($password, PASSWORD_DEFAULT);
        if (password_verify($password, $row['passwordHash'])) {   // Using PHP 5.5's password_verify() function to check password
            $_SESSION['user_name'] = $row['name'];
            echo "Session Name = ".$_SESSION['user_name']."<br>";
            $_SESSION['user_email'] = $row['email'];
            $_SESSION['user_is_logged_in'] = true;
            return "";  // Success if empty string
        } return "Wrong password.";
    } return "This user does not exist.";
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
