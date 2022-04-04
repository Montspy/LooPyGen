<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Getting Your Private Key</h3>
        <div id="guide">
            <div>
                <p>Export your account info from the web or mobile wallet and paste your Private Key into the field below.</p>
            </div>
        </div>
        <form method="post" action="/config/1">
            <h3>Artist Info</h3>
            <div id="artist" class="section">
                <input required type="text" class="form wide" id="minter" name="minter" placeholder="Wallet Address, ENS, or Account ID" />
                <input required type="text" class="form wide" id="private_key" name="private_key" placeholder="Private Key" />
                <div class="row">
                    <select required class="form med" id="nft_type" name="nft_type">
                        <option value="0">EIP-1155</option>
                        <option value="1">EIP-721</option>
                    </select>
                    <select required class="form med" id="fee_token" name="fee_token">
                        <option value="1">LRC</option>
                        <option value="0">ETH</option>
                    </select>
                </div>
            </div>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="FINISH" />
        </form>
    <?php } else {
        $minter = $_POST['minter'];
        $private_key = $_POST['private_key'];
        $nft_type = $_POST['nft_type'];
        $fee_token = $_POST['fee_token'];
        $config_file = "./config.json";

        $config_data = array("minter"=>$minter,
                             "private_key"=>$private_key,
                             "nft_type"=>(int)$nft_type,
                             "fee_token"=>(int)$fee_token);

        $config_json = json_encode($config_data, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents($config_file, $config_json);

        Redirect('/config/edit', false);
    }

?>