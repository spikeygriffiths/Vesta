<?php 
session_start();    // start the session, always needed, and must be before any HTML tags
error_reporting(E_ALL); 
if ($_SESSION['user_is_logged_in'] == true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta.php\"/>"; # Automatically go to main page if we're logged in
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
        if (0 == $numUsers) {
            $_SESSION['user_is_logged_in'] = true;  # Log in without a name (we have no names yet...)
            echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta.php\"/>"; # Automatically go to home page if there are no registered users
        } else {
            $this->PerformUserLoginAction($db);            // check for possible user interactions (login with session/post data or logout)
            if ($_SESSION['user_is_logged_in'] == true) {
                echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta.php\"/>"; # Automatically go to home page once we're logged in
            } else {
                $this->ShowPageLoginForm();
            }
        }
    }

    private function PerformUserLoginAction($db)
    {
        if (!empty($_SESSION['user_name']) && ($_SESSION['user_is_logged_in'])) {
            //$this->DoLoginWithSessionData();
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

echo "<html><head>";
echo "<link rel=\"icon\" type=\"image/ico\" href=\"/favicon.ico\"/>";   # Not sure if this is necessary, but does no harm...
echo "</head><body>";
echo "<center><img src='vestaTitle.png' width=128 height=128><br>";
$app = new OneFileLoginApplication();
echo "</body></html>";

?>
