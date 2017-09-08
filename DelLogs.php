<?php
array_map('unlink', glob("/home/pi/Vesta/*_err.log"));
echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index after removing logs
?>
