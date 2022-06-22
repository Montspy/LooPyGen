<?php

    $version = file_get_contents('./.version');
    $mint_config = "./.secrets/config.json";
    $transfer_config = "./.secrets/transfer_config.json";
    $progress_file = "./php/progress.json";

    if (!empty($_GET['page'])) {
        $page = $_GET['page'];
    } else {
        $page = "home";
    }

    require 'php/functions.php';

    if (!empty($_POST['redirect'])) {
        $redirect = $_POST['redirect'];
    } else {
        $redirect = "FALSE";
    }

    if ($page === "mint-config" or $page === "transfer-config" or $page === "setup" or $page === "edit") {
        $page = "$page/1";
    }

    if ($redirect !== "TRUE") {
        include "php/header.html"; ?>
        <div class="content">
            <h1><a href="/">LooPyGen</a> v<?php echo $version ?></h1>
            <?php include "php/$page.php"; ?>
        </div>
    <?php } else {
        include "php/$page.php";
    }

    include "php/footer.php";

?>