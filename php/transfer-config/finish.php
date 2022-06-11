<?php

    if (!file_exists($transfer_config)) {
        $config = json_decode($transfer_config, true);
    } else {
        Redirect('/transfer-config/1', false);
    }

    if (!empty($config)) { ?>
        <h3>Transfer Configuration Settings Saved</h3>
        <div id="guide">
            <section>
                <p><b>Sender (Address, ENS, or Account ID)</b>: <?php echo $config['sender'] ?></p>
                <p><b>L2 Private Key</b>: <?php echo str_repeat("*", strlen($config['private_key'])) ?></p>
                <p><b>L1 Private Key</b>: <?php echo str_repeat("*", strlen($config['private_key_mm'])) ?></p>
                <p><b>Fee Token</b>: <?php echo $config['fee_token'] ?></p>
            </section>
        </div>
        <div class="nav">
            <a href="/">Back to Home</a>
        </div>
    <?php } else {
        Redirect('/transfer-config/1', false);
    }

?>