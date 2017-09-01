<?php
session_start();
include "database.php";

$db = DatabaseInit();
$event = $_SESSION['user_name']." Logged out";
NewEvent(0, $event, $db);
$_SESSION['user_is_logged_in'] = false;
echo "<meta http-equiv=\"refresh\" content=\"0;url=/index.php\"/>"; # Automatically go to index when we're not logged in

?>
