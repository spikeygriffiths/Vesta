<?php
session_start();
error_reporting(E_ALL); 
include "database.php";
if ($_SESSION['user_is_logged_in'] != true) echo "<meta http-equiv=\"refresh\" content=\"0;url=/vesta/index.php\"/>"; # Automatically go to index if we're not logged in

// Following code is freely adapted from:
// @link https://github.com/panique/php-login-one-file/
// @license http://opensource.org/licenses/MIT MIT License
class Register
{
    public $feedback = "";

    public function __construct()
    {
        $db = DatabaseInit();
        $this->DoRegistration($db);
        $this->ShowPageRegistration();
    }

    private function DoRegistration($db)
    {
        if ($this->CheckRegistrationData()) {
            $this->CreateNewUser($db);
        }
        return false;   // default return
    }

    private function CheckRegistrationData()
    {
        $faultStr = "";
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
        $name = htmlentities($_POST['user_name'], ENT_QUOTES);        // remove html code etc. from username and email
        $email = htmlentities($_POST['user_email'], ENT_QUOTES);
        $password = $_POST['user_password_new'];
        // crypt the user's password with the PHP 5.5's password_hash() function, results in a 60 char hash string.
        // the constant PASSWORD_DEFAULT comes from PHP 5.5 or the password_compatibility_library
        $passwordHash = password_hash($password, PASSWORD_DEFAULT);
        $this->feedback = CreateUser($name, $email, $passwordHash, $db);    // See database.php.  Returns string describing result
    }

    private function ShowPageRegistration()
    {
        if ($this->feedback) {
            echo $this->feedback . "<br><br>";
        }
        echo '<h2>Registration</h2>';
        echo '<form method="post" action="' . $_SERVER['SCRIPT_NAME'] . '?action=register" name="registerform">';
        echo '<label title="(only letters and numbers, 2 to 64 characters)" for="login_input_username">Username</label>';
        echo '<input id="login_input_username" type="text" pattern="[a-zA-Z0-9]{2,64}" name="user_name" required /><br><br>';
        echo '<label for="login_input_email">User\'s email</label>';
        echo '<input id="login_input_email" type="email" name="user_email" required /><br><br>';
        echo '<label title="(min. 6 characters)" for="login_input_password_new">Password</label>';
        echo '<input id="login_input_password_new" class="login_input" type="password" name="user_password_new" pattern=".{6,}" required autocomplete="off" /><br><br>';
        echo '<label for="login_input_password_repeat">Repeat password</label>';
        echo '<input id="login_input_password_repeat" class="login_input" type="password" name="user_password_repeat" pattern=".{6,}" required autocomplete="off" /><br><br>';
        echo '<input type="submit" name="register" value="Register" />';
        echo '</form>';
    }
}

echo "<html><head>";
echo "</head><body>";
echo "<center><img src='vestaTitle.png' title=\"Vesta was the Roman goddess of hearth and home\" width=128 height=128><br>";
$app = new Register();
echo "<button type=\"button\" onclick=\"window.location.href='/vesta/index.php'\">Home</button><br><br>";
echo "</body></html>";

?>

