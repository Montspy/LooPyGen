<?php $short_hash = shell_exec('git rev-parse --short HEAD');

    if (!empty($_GET['page'])) {
        $step = $_GET['page'];
    } else {
        $step = 1;
    }

    function Redirect($url, $permanent = false) {
        header('Location: ' . $url, true, $permanent ? 301 : 302);
        exit();
    }

    if (!empty($_POST['redirect'])) {
        $redirect = $_POST['redirect'];
    } else {
        $redirect = "FALSE";
    }

    if ($redirect !== "TRUE") {
        include "php/header.html"; ?>
        <div class="content">
            <h2>LooPyGen UI ( <?php echo $short_hash ?>)</h2>
            <?php include "php/$step.php"; ?>
        </div>
    <?php } else {
        include "php/$step.php";
    }

    include "php/footer.html";
?>