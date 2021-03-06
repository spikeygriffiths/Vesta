<?php
// database.php
if (PHP_SESSION_ACTIVE != session_status()) session_start();
//session_start();

function GetDbFileName()
{
    return "vesta.db";
}

function DatabaseInit()
{
    if ((file_exists(GetDbFileName())) || (readlink(GetDbFileName()))) {
        try {
            $db = new PDO("sqlite:".GetDbFileName());
        } catch (PDOException $e) {
            die("Can't open ".GetDbFileName()." (".$e->getMessage().")");
        }
        return $db;
    } else echo GetDbFileName()," doesn't exist!<br>";
    die("Can't find database at ".GetDbFileName());
}

function GetDbFileSize()
{
    return filesize(GetDbFileName());
}

function GetCount($db, $table, $qualifier = "")
{
    if ($qualifier == "") {
        $result = $db->query("SELECT COUNT(*) FROM ".$table);
    } else {
        $result = $db->query("SELECT COUNT(*) FROM ".$table." WHERE ".$qualifier);  # $qualifier may be "devKey= 21" or "timestamp<('now','-2 days')", etc.
    }
    if ($result != null) {
        return $result->fetchColumn();
    }
    return null;
}

function GetDevCount($db)
{
    return GetCount($db, "Devices");
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

function GetDevKeyFromItem($item, $value, $db)
{
    $result = $db->query("SELECT devKey FROM Devices WHERE ".$item."=\"".$value."\" COLLATE NOCASE");
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch["devKey"];
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

function GetTimedLoggedItem($item, $devKey, $time, $db) # For Battery, Signal, Presence, Temperature, PowerReadingW, etc.
{
    $result = $db->query("SELECT * FROM ".$item." WHERE devKey=".$devKey." AND timestamp > ".$time." LIMIT 1");  # Get first item after time
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        return $fetch;  # Return value and time
    }
    return null;
}

function GetLatestLoggedItem($item, $devKey, $db)
{
    $result = $db->query("SELECT * FROM ".$item." WHERE devKey=".$devKey." ORDER BY ROWID DESC LIMIT 1");  # Get last item
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        return $fetch;  # Return value and time
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

function GetConfig($item, $default, $db)
{
    $result = $db->query("SELECT value FROM Config WHERE item=\"".$item."\"");
    if ($result != null) {
        $result->setFetchMode(PDO::FETCH_ASSOC);
        $fetch = $result->fetch();
        if ($fetch != null) {
            return $fetch["value"];
        }
    }
    //if (!$default) $default = ""; # Ensure we have something as a default so we can set the value
    $db->exec("INSERT OR REPLACE INTO Config VALUES(\"".$item."\",\"".$default."\")");
    return $default;
}

function SetConfig($item, $value, $db)
{
    if ($item != "NewItem") { // If item exists
        if ($value != "") {
            $query = "UPDATE Config SET value=\"".$value."\" WHERE item=\"".$item."\""; # Update existing value
        } else {
            $query = "DELETE FROM Config WHERE item=\"".$item."\"";  # Remove item if value is empty
        }
    } else { // New Item requested
        $query = "INSERT INTO Config (item) VALUES(\"".$value."\")";  # Add new configuration item (named $value), with empty value
    }
    echo "About to send ",$query, " to DB<br>";
    $db->exec($query);
}

function GetVariable($name, $default, $db)
{
    $sth = $db->prepare("SELECT value FROM Variables where name=\"".$name."\"");
    $sth->execute();
    $row = $sth->fetch();
    if ($row != null) {
        return $row['value'];
    }
    SetVariable($name, $default, $db);
    return $default;
}

function SetVariable($name, $val, $db)
{
    $now = date('Y-m-d H:i:s');
    $db->exec("INSERT OR REPLACE INTO Variables VALUES(\"".$name."\",\"".$val."\",\"".$now."\")");
}

?>
