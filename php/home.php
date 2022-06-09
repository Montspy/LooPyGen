<section class="nav">
    <h3>Configuration Setup</h3>
    <a href="/setup/1"><span class="material-icons">create_new_folder</span> CREATE NEW COLLECTION</a>
    <a href="/edit/1"><span class="material-icons">edit</span> EDIT EXISTING COLLECTION</a>
    <a href="/mint-config/1"><span class="material-icons">settings_suggest</span> MINTING CONFIG SETUP</a>
    <a href="/transfer-config/1"><span class="material-icons">settings</span> TRANSFER CONFIG SETUP</a>
</section>

<section class="nav">
    <h3>Collection Actions</h3>
    <a href="/collection/images"><span class="material-icons">photo_library</span> GENERATE IMAGES</a>
    <a href="/collection/metadata"><span class="material-icons">data_object</span> GENERATE METADATA</a>
    <a href="/collection/mint"><span class="material-icons">publish</span> MINT COLLECTION</a>
    <a href="/collection/transfer"><span class="material-icons">keyboard_double_arrow_right</span> TRANSFER COLLECTION</a>
</section>

<section class="nav">
    <h3>Other Actions</h3>
    <!-- <a href="/prepare">PREPARE METADATA</a> -->
    <a href="/mint"><span class="material-icons">publish</span> MINT SINGLE ITEM</a>
    <a href="/transfer"><span class="material-icons">keyboard_double_arrow_right</span> TRANSFER</a>
    <a href="/home?nuke=engage" class="danger"><span class="material-icons">dangerous</span> NUKE SENSITIVE INFO</a>
    <!-- <a href="/home?update=true">UPDATE LOOPYGEN</a> -->
</section>

<?php

    if (!empty($_GET['nuke'])) {
        if (file_exists("./config.json")) { unlink("./config.json"); }
        if (file_exists("./transfer_config.json")) { unlink("./transfer_config.json"); }
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