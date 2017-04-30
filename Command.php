<?php
error_reporting(E_ALL); 
include "HubCmd.php";

if (isset($_GET['cmd'])) {
    $cmd = $_GET['cmd'];
} else {
    $cmd = $_POST['cmd'];
}
if (isset($_GET['expRsp'])) {
    $expRsp = $_GET['expRsp'];
    if ($expRsp) {
        $ans = HubCmd($cmd, true);  // Don't know how to post $ans back to caller?
    } else {
        HubCmd($cmd, false);
    }
} else {
    HubCmd($cmd, false);
}

header('location:'.$_SERVER['HTTP_REFERER']);
?>

