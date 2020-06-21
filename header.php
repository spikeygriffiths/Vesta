<?php
if (PHP_SESSION_ACTIVE != session_status()) session_start();
//session_start();

if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in
echo "<html><head>";    // NB This header file also starts the html head tag (but doesn't end it, to allow pages to extend the head)
echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">";  # So it works on mobile phones as well as laptops
echo "<link rel=\"shortcut icon\" type=\"image/x-icon\" href=\"/vesta/favicon.ico\">"; # Note that favicon isn't in the root, but is in the "vesta" sub-directory
echo "<link rel=\"stylesheet\" type=\"text/css\" href=\"/vesta/vesta.css\">";
?>
