<?php

    $config_file = file_get_contents("./transfer_config.json");
    if (!file_exists($config_file)) {
        $config = json_decode($config_file, true);
    } else {
        Redirect('/transfer/1', false);
    }

    if (!empty($config)) { ?>
        <h3>Transfer Configuration Settings Saved</h3>
        <div id="guide">
            <div class="section">
                <p><b>Sender (Address, ENS, or Account ID)</b>: <?php echo $config['sender'] ?></p>
                <p><b>L2 Private Key</b>: <?php echo str_repeat("*", strlen($config['private_key'])) ?></p>
                <p><b>L1 Private Key</b>: <?php echo str_repeat("*", strlen($config['private_key_mm'])) ?></p>
                <p><b>Fee Token</b>: <?php echo $config['fee_token'] ?></p>
            </div>
        </div>
        <a href="/"><button class="btn">Back to Home</button></a>
    <?php } else {
        Redirect('/transfer/1', false);
    }

?>