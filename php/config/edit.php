<?php

    $config_file = file_get_contents("./config.json");
    if (!file_exists($config_file)) {
        $config = json_decode($config_file, true);
    } else {
        Redirect('/config/1', false);
    }

    if (!empty($config)) { ?>
        <h3>Configuration Settings</h3>
        <div id="guide">
            <div class="section">
                <p><b>Minting Address</b>: <?php echo $config['mint_address'] ?></p>
                <p><b>Private Key</b>: <?php echo $config['private_key'] ?></p>
                <p><b>Account ID</b>: <?php echo $config['acct_id'] ?></p>
                <p><b>NFT Type</b>: <?php echo $config['nft_type'] ?></p>
                <p><b>Fee Token</b>: <?php echo $config['fee_token'] ?></p>
            </div>
        </div>
    <?php } else {
        Redirect('/config/1', false);
    }

?>