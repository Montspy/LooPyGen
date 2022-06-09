<?php

    $config_file = file_get_contents("./config.json");
    if (!file_exists($config_file)) {
        $config = json_decode($config_file, true);
    } else {
        Redirect('/mint-config/1', false);
    }

    if (!empty($config)) { ?>
        <h3>Configuration Settings</h3>
        <div id="guide">
            <section>
                <p><b>Minter (Address, ENS, or Account ID)</b>: <?php echo $config['minter'] ?></p>
                <p><b>Private Key</b>: <?php echo str_repeat("*", strlen($config['private_key'])) ?></p>
                <p><b>Royalty Percentage</b>: <?php echo $config['royalty_percentage'] ?></p>
                <p><b>NFT Type</b>: <?php echo $config['nft_type'] ?></p>
                <p><b>Fee Token</b>: <?php echo $config['fee_token'] ?></p>
            </section>
        </div>
        <div class="nav"><a href="/">Back to Home</a></div>
    <?php } else {
        Redirect('/mint-config/1', false);
    }

?>