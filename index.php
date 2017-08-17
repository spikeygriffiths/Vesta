<?php 
session_start();    // start the session, always needed, and must be before any HTML tags
error_reporting(E_ALL); 
include "database.php";

/*echo "<html><head>";
echo "<link rel=\"icon\" type=\"image/ico\" href=\"/favicon.ico\"/>";   # Not sure if this is necessary, but does no harm...
echo "</head><body>";
echo "<center><img src='vestaTitle.png' width=128 height=128><br>";
echo "</body></html>";*/

// Following code is taken from:
// @author Panique
// @link https://github.com/panique/php-login-one-file/
// @license http://opensource.org/licenses/MIT MIT License
class OneFileLoginApplication
{
    public $feedback = "";

    public function __construct()
    {
        echo "Starting<br>";
        $this->RunApplication();
    }

    public function RunApplication()
    {
        // check if user wants to see register page (etc.)
        $db = DatabaseInit();
        if (isset($_GET["action"]) && $_GET["action"] == "register") {
            $this->DoRegistration($db);
            $this->ShowPageRegistration();
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
        if (isset($_GET["action"]) && $_GET["action"] == "logout") {
            $this->DoLogout();
        } elseif (!empty($_SESSION['user_name']) && ($_SESSION['user_is_logged_in'])) {
            $this->DoLoginWithSessionData();
        } elseif (isset($_POST["login"])) {
            $this->DoLoginWithPostData($db);
        }
    }

    private function DoLoginWithPostData($db)
    {
        if ($this->CheckLoginFormDataNotEmpty()) {
            $name = $_POST['user_name'];
            $password = $_POST['user_password'];
            CheckPasswordCorrectnessAndLogin($name, $password, $db);
            print_r($_SESSION);
        }
    }

    private function DoLogout()
    {
        $_SESSION['user_is_logged_in'] = false;
        $this->feedback = "You were just logged out.";
    }

    private function DoRegistration($db)
    {
        if ($this->CheckRegistrationData()) {
            $this->CreateNewUser($db);
        }
        return false;   // default return
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

    private function CheckRegistrationData()
    {
        $faultStr = "";
        if (!isset($_POST["register"])) return false;        // if no registration form submitted: exit the method
        if (empty($_POST['user_name'])) {
            $faultStr = "Empty Username";
        } elseif (empty($_POST['user_password_new']) || empty($_POST['user_password_repeat'])) {
            $faultStr = "Empty Password";
        } elseif ($_POST['user_password_new'] !== $_POST['user_password_repeat']) {
            $faultStr = "Password and password repeat are not the same";
        } elseif (strlen($_POST['user_password_new']) < 6) {
            $faultStr = "Password has a minimum length of 6 characters";
        } elseif (strlen($_POST['user_name']) > 64 || strlen($_POST['user_name']) < 2) {
            $faultStr = "Username cannot be shorter than 2 or longer than 64 characters";
        } elseif (!preg_match('/^[a-z\d]{2,64}$/i', $_POST['user_name'])) {
            $faultStr = "Username does not fit the name scheme: only a-Z and numbers are allowed, 2 to 64 characters";
        } elseif (empty($_POST['user_email'])) {
            $faultStr = "Email cannot be empty";
        } elseif (strlen($_POST['user_email']) > 64) {
            $faultStr = "Email cannot be longer than 64 characters";
        } elseif (!filter_var($_POST['user_email'], FILTER_VALIDATE_EMAIL)) {
            $faultStr = "Your email address is not in a valid email format";
        }
        $this->feedback = $faultStr;
        return ($faultStr == "");  // Did we note any fault?
    }

    private function CreateNewUser($db)
    {
        $faultStr = "";
        $name = htmlentities($_POST['user_name'], ENT_QUOTES);        // remove html code etc. from username and email
        $email = htmlentities($_POST['user_email'], ENT_QUOTES);
        $password = $_POST['user_password_new'];
        // crypt the user's password with the PHP 5.5's password_hash() function, results in a 60 char hash string.
        // the constant PASSWORD_DEFAULT comes from PHP 5.5 or the password_compatibility_library
        $passwordHash = password_hash($user_password, PASSWORD_DEFAULT);
        echo "About to create user ".$name.", email ".$email.", with hash of ".$passwordHash."<br>";
        $faultStr =  CreateUser($name, $email, $passwordHash, $db);    // See database.php.  Returns string.  If empty, then is successful
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
        echo '<label for="login_input_username">Username (or email)</label> ';
        echo '<input id="login_input_username" type="text" name="user_name" required /><br> ';
        echo '<label for="login_input_password">Password</label> ';
        echo '<input id="login_input_password" type="password" name="user_password" required /><br> ';
        echo '<input type="submit"  name="login" value="Log in" />';
        echo '</form>';
        echo '<a href="' . $_SERVER['SCRIPT_NAME'] . '?action=register">Register new account</a>';
    }

    private function ShowPageRegistration()
    {
        if ($this->feedback) {
            echo $this->feedback . "<br><br>";
        }
        echo '<h2>Registration</h2>';
        echo '<form method="post" action="' . $_SERVER['SCRIPT_NAME'] . '?action=register" name="registerform">';
        echo '<label for="login_input_username">Username (only letters and numbers, 2 to 64 characters)</label>';
        echo '<input id="login_input_username" type="text" pattern="[a-zA-Z0-9]{2,64}" name="user_name" required /><br>';
        echo '<label for="login_input_email">User\'s email</label>';
        echo '<input id="login_input_email" type="email" name="user_email" required /><br>';
        echo '<label for="login_input_password_new">Password (min. 6 characters)</label>';
        echo '<input id="login_input_password_new" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" /><br>';
        echo '<label for="login_input_password_repeat">Repeat password</label>';
        echo '<input id="login_input_password_repeat" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" /><br>';
        echo '<input type="submit" name="register" value="Register" />';
        echo '</form>';
        echo '<a href="' . $_SERVER['SCRIPT_NAME'] . '">Homepage</a>';
    }
}
$app = new OneFileLoginApplication();
?>
