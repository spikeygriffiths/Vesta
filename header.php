<?php 
session_start();
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
error_reporting(E_ALL); 
echo "<html><head>";    // NB This header file also starts the html head tag (but doesn't end it, to allow pages to extend the head)
echo "<link rel=\"shortcut icon\" type=\"image/x-icon\" href=\"favicon.ico\">"; # Note that favicon isn't in the root, but is in the "vesta" sub-directory
?>
