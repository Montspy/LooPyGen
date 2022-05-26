<div class="section">
    <h3>Configuration Setup</h3>
    <a href="/setup/1"><button class="btn">CREATE NEW COLLECTION</button></a>
    <a href="/edit/1"><button class="btn">EDIT EXISTING COLLECTION</button></a>
    <a href="/config/1"><button class="btn">MINT & TRANSFER CONFIG SETUP</button></a>
</div>

<div class="section">
    <h3>Collection Actions</h3>
    <a href="/generate/images"><button class="btn">GENERATE IMAGES</button></a>
    <a href="/generate/metadata"><button class="btn">GENERATE METADATA</button></a>
    <a href="/mint/1?type=collection"><button class="btn">MINT COLLECTION</button></a>
</div>

<div class="section">
    <h3>Other Actions</h3>
    <a href="/prepare"><button class="btn">PREPARE METADATA</button></a>
    <a href="/mint/1?type=single"><button class="btn">MINT SINGLE ITEM</button></a>
    <!-- <a href="/transfer/1"><button class="btn">TRANSFER</button></a> -->
    <a href="/home?nuke=engage"><button class="btn">NUKE SENSITIVE INFO</button></a>
</div>

<?php

    if (!empty($_GET['nuke'])) {
        unlink("./config.json");
        echo "<h3><i>Sensitive Info Deleted</i></h3>";
    }

?>