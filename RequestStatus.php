<?php
include "AppCmd.php";
include "header.php";   # Has other includes as well as log-out detection, and favicon.  NB Has "<html><head>" for favicon link!
echo "</head><body>";
ini_set('display_errors', '1');

echo AppCmd("synopsis", False);    # Build status page
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/synopsis.html\"/>";  # And then display it
echo "</body></html>";
?>
