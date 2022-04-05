<?php

    $short_hash = shell_exec('git rev-parse --short HEAD');

    if (!empty($_GET['page'])) {
        $page = $_GET['page'];
    } else {
        $page = "home";
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

    if ($page === "config" or $page === "setup") {
        $page = "$page/1";
    }

    if ($redirect !== "TRUE") {
        include "php/header.html"; ?>
        <div class="content">
            <h1><a href="/">LooPyGen UI</a> ( <?php echo $short_hash ?>)</h1>
            <?php include "php/$page.php"; ?>
        </div>
    <?php } else {
        include "php/$page.php";
    }

    include "php/footer.html";

?>