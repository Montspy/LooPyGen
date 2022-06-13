<?php

    if (!file_exists($mint_config) or !isset($_GET['result'])) {
        BrowserRedirect('/mint-config/1');
    }

    if ($_GET['result'] === "0") { ?>
        <h3 class="success">Configuration Successfully Encrypted</h3>
        <div id="guide">
            <section>
                <p>Your configuration is encrypted stored in a secure location that gets destroyed when you remove or update LooPyGen.</p>
                <p>If you forget your passphrase for any reason, or need to change the private key to another wallet, simply remake your config again with a new passphrase.</p>
            </section>
        </div>
        <div class="nav"><a href="/">Back to Home</a></div>
        <div class="nav"><a href="/mint-config/1">Remake Config</a></div>
    <?php } else {
        unlink($mint_config); ?>
        <h3 class="error">Configuration Not Encrypted</h3>
        <div id="guide">
            <section>
                <p>Your configuration was not encrypted and has been removed from the system.</p>
                <p>Please try again.</p>
            </section>
        </div>
        <div class="nav"><a href="/mint-config/1">Retry Config</a></div>
    <?php }

?>