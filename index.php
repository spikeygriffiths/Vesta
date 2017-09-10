<?php 
session_start();    // start the session, always needed, and must be before any HTML tags
error_reporting(E_ALL);
include "database.php";

// Following code is freely adapted from:
// @link https://github.com/panique/php-login-one-file/
// @license http://opensource.org/licenses/MIT MIT License
class OneFileLoginApplication
{
    public $feedback = "";

    public function __construct()
    {
        $db = DatabaseInit();
        $numUsers = GetNumUsers($db);
        if (0 == $numUsers) {   # If we have no users yet
            $_SESSION['user_is_logged_in'] = true;  # Log in without a name (we have no names yet...)
            echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/vesta.php\"/>"; # Automatically go to home page if there are no registered users
        } else {
            $this->PerformUserLoginAction($db);            // check for possible user interactions (login with session/post data or logout)
            if ($_SESSION['user_is_logged_in'] == true) {
                $event = $_SESSION['user_name']." Logged in";
                NewEvent(0, $event, $db);
                echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/vesta.php\"/>"; # Automatically go to home page once we're logged in
            } else {
                $this->ShowPageLoginForm();
            }
        }
    }

    private function PerformUserLoginAction($db)
    {
        if (!empty($_SESSION['user_name']) && ($_SESSION['user_is_logged_in'])) {
            echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/vesta.php\"/>"; # Automatically go to home page if we're already logged in
        } elseif (isset($_POST["login"])) {
            $this->DoLoginWithPostData($db);
        }
    }

    private function DoLoginWithPostData($db)
    {
        if ($this->CheckLoginFormDataNotEmpty()) {
            $name = $_POST['user_name'];
            $password = $_POST['user_password'];
            $faultStr = CheckPasswordCorrectnessAndLogin($name, $password, $db);
            $this->feedback = $faultStr;
            return ($faultStr == "");  // Did we note any fault?
        }
    }

    private function CheckLoginFormDataNotEmpty()
    {
        $faultStr = "";
        if (empty($_POST['user_name'])) {
            $faultStr = "Username field was empty.";
        } elseif (empty($_POST['user_password'])) {
            $faultStr = "Password field was empty.";
        }
        $this->feedback = $faultStr;
        return ($faultStr == "");  // Did we note any fault?
    }

    private function ShowPageLoginForm()
    {
        if ($this->feedback) {
            echo $this->feedback . "<br><br>";
        }
        echo '<h2>Login</h2>';
        echo '<form method="post" action="' . $_SERVER['SCRIPT_NAME'] . '" name="loginform">';
        echo '<label for="login_input_username">Username</label> ';
        echo '<input id="login_input_username" type="text" name="user_name" required /><br><br>';
        echo '<label for="login_input_password">Password</label> ';
        echo '<input id="login_input_password" type="password" name="user_password" required /><br><br>';
        echo '<input type="submit"  name="login" value="Log in" />';
        echo '</form>';
    }
}

if ($_SESSION['user_is_logged_in'] == true) {
    echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/vesta.php\"/>"; # Automatically go to main page if we're logged in
} else {
    $user = $_SESSION['user_name'];
    /*if (strlen($user) == 0) {   # Check if PHP's garbage collector has logged us out
        $event = "Last user Timed out"; # Only works when page is refreshed, and always writes two entries, so is not much use
        $db = DatabaseInit();
        NewEvent(0, $event, $db);
    }*/
    echo "<html><head>";
    echo "<link rel=\"shortcut icon\" type=\"image/x-icon\" href=\"favicon.ico\">"; # Seems to be necessary
    echo "</head><body>";
    echo "<center><img src='vestaTitle.png' title=\"Vesta was the Roman goddess of hearth and home\" width=128 height=128><br>";
    $app = new OneFileLoginApplication();
    echo "</body></html>";
}

?>
