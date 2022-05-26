<div class="section">
    <h3>Configuration Setup</h3>
    <a href="/setup/1"><button class="btn">CREATE NEW COLLECTION</button></a>
    <!-- <a href="/edit/view"><button class="btn">EDIT EXISTING COLLECTION</button></a> -->
    <a href="/config/1"><button class="btn">MINTING CONFIG SETUP</button></a>
</div>

<div class="section">
    <h3>Collection Actions</h3>
    <a href="/collection/images"><button class="btn">GENERATE IMAGES</button></a>
    <a href="/collection/metadata"><button class="btn">GENERATE METADATA</button></a>
    <a href="/collection/mint"><button class="btn">MINT COLLECTION</button></a>
</div>

<div class="section">
    <h3>Other Actions</h3>
    <!-- <a href="/prepare"><button class="btn">PREPARE METADATA</button></a> -->
    <!-- <a href="/mint/1?type=single"><button class="btn">MINT SINGLE ITEM</button></a> -->
    <!-- <a href="/transfer/1"><button class="btn">TRANSFER</button></a> -->
    <a href="/home?nuke=engage"><button class="btn">NUKE SENSITIVE INFO</button></a>
    <!-- <a href="/home?update=true"><button class="btn">UPDATE LOOPYGEN</button></a> -->
</div>

<?php

    if (!empty($_GET['nuke'])) {
        unlink("./config.json");
        if (file_exists("./config.json")) {
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