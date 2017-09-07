<?php
error_reporting(E_ALL); 
include "AppCmd.php";

if (isset($_GET['cmd'])) {
    $cmd = $_GET['cmd'];
} else {
    $cmd = $_POST['cmd'];
}
if (isset($_GET['expRsp'])) {
    $expRsp = $_GET['expRsp'];
    if ($expRsp) {
        $ans = AppCmd($cmd, true);  // Don't know how to post $ans back to caller?
    } else {
        AppCmd($cmd, false);
    }
} else {
    AppCmd($cmd, false);
}

header('location:'.$_SERVER['HTTP_REFERER']);
?>

