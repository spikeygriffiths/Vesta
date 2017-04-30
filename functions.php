<?php
// functions.php
// Useful functions for talking to hubapp

function ConnectToHub($addr, $port)
{
    $sck = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
    if ($sck != false) {
        if (socket_connect($sck, $addr, $port) != false) {
            return $sck;
        } else echo "Socket_connect failed with ". socket_strerror(socket_last_error($sck)) . "<br>";
    } else echo "Socket_create failed with ". socket_strerror(socket_last_error()) . "<br>";
    return false;
}

function HubCmd($cmd) // Takes a command for the hub and returns any string
{
    $hubSck = ConnectToHub("127.0.0.1", 12345);
    if ($hubSck != false) {
        socket_write($hubSck, $cmd, strlen($cmd));
        $ans = socket_read($hubSck, 1024);
        socket_close($hubSck);
        return $ans;
    } else echo "Socket  connection failed!<br>";
}
?>

