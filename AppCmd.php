<?php

function ConnectToApp($addr, $port)
{
    $sck = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    if ($sck != false) {
        if (socket_connect($sck, $addr, $port) != false) {
            return $sck;
        } else echo "Socket_connect failed with ". socket_strerror(socket_last_error($sck)) . "<br>";
    } else echo "Socket_create failed with ". socket_strerror(socket_last_error()) . "<br>";
    return false;
}

function AppCmd($cmd, $expRsp) // Takes a command for the app and returns any string
{
    $appSck = ConnectToApp("127.0.0.1", 12345); # Local machine, Vesta port
    if ($appSck != false) {
        socket_write($appSck, $cmd, strlen($cmd));
        if ($expRsp) {
            $ans = socket_read($appSck, 1024);
        } else $ans = "";
        socket_close($appSck);
        return $ans;
    } else return "Socket  connection failed!<br>";
}
?>

