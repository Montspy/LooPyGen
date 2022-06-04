<section class="nav">
    <h3>Configuration Setup</h3>
    <a href="/setup/1">CREATE NEW COLLECTION</a>
    <!-- <a href="/edit/view">EDIT EXISTING COLLECTION</a> -->
    <a href="/config/1">MINTING CONFIG SETUP</a>
    <a href="/transfer/1">TRANSFER CONFIG SETUP</a>
</section>

<section class="nav">
    <h3>Collection Actions</h3>
    <a href="/collection/images">GENERATE IMAGES</a>
    <a href="/collection/metadata">GENERATE METADATA</a>
    <a href="/collection/mint">MINT COLLECTION</a>
    <a href="/collection/transfer">TRANSFER COLLECTION</a>
</section>

<section class="nav">
    <h3>Other Actions</h3>
    <!-- <a href="/prepare">PREPARE METADATA</a> -->
    <a href="/mint">MINT SINGLE ITEM</a>
    <!-- <a href="/transfer/1">TRANSFER</a> -->
    <a href="/home?nuke=engage">NUKE SENSITIVE INFO</a>
    <!-- <a href="/home?update=true">UPDATE LOOPYGEN</a> -->
</section>

<?php

    if (!empty($_GET['nuke'])) {
        unlink("./config.json");
        unlink("./transfer_config.json");
        if (file_exists("./config.json") || file_exists("./transfer_config.json")) {
            echo "<h3 class='error'><i>Error: Sensitive info not deleted</i></h3>";
        } else {
            echo "<h3 class='success'><i>Success: Sensitive Info Deleted</i></h3>";
        }
    }

    if (!empty($_GET['update'])) {
        exec('git pull --recurse-submodules', $output, $code);
        echo "<pre>";
        echo "Update Exit Code: ${code}";
        echo "";
        foreach ($output as $line) {
            echo $line;
        }
        echo "</pre>";
    }

?>