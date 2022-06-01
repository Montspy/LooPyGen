<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Getting Your L1 and L2 Private Keys</h3>
        <div id="guide">
            <div>
                <p>STEP 01 - Export your Loopring account info to get your Loopring Private Key.</p>
                <ol>
                    <li>Login to the <a href="https://loopring.io/#/layer2" target="_blank">Loopring Wallet</a></li>
                    <li>Go to <b>L2 Wallet -> Security -> Export Account</b></p></li>
                </ol>
                <p>STEP 02 - Export your L1 Private Key from Metamask.</p>
                <ol>
                    <li>Follow <a href="https://metamask.zendesk.com/hc/en-us/articles/360015289632-How-to-Export-an-Account-Private-Key" target="_blank">this guide</a></li>
                </ol>
            </div>
        </div>
        <form method="post" action="/transfer/1">
            <h3>Transfer Tool Info</h3>
            <div id="artist" class="section">
                <div data-tooltip="From Address: The L2 wallet address or ENS or Account ID of the MetaMask wallet sending the NFTs"><input required type="text" class="form wide" id="sender" name="sender" placeholder="From Address, ENS, or Account ID" /></div>
                <div data-tooltip="Loopring L2 Private Key: The Loopring private key of the from address [DO NOT SHARE THIS INFO WITH ANYONE]"><input required type="password" class="form wide" id="private_key" name="private_key" placeholder="Loopring L2 Private Key (from step 01)" /></div>
                <div data-tooltip="MetaMask L1 Private Key: The MetaMask private key of the from address [DO NOT SHARE THIS INFO WITH ANYONE]"><input required type="password" class="form wide" id="private_key_mm" name="private_key_mm" placeholder="MetaMask L1 Private Key (from step 02)" /></div>
                <div class="row">
                    <div data-tooltip="Fee Token: The token to be used to pay protocol fees">
                        <label for="fee_token" class="med">
                            Fee Token:
                        </label>
                        <select required class="form med" id="fee_token" name="fee_token">
                            <option value="1">LRC</option>
                            <option value="0">ETH</option>
                        </select>
                    </div>
                </div>
            </div>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="FINISH" />
        </form>
    <?php } else {
        $sender = $_POST['sender'];
        $private_key = $_POST['private_key'];
        $private_key_mm = $_POST['private_key_mm'];
        $fee_token = $_POST['fee_token'];
        $config_file = "./transfer_config.json";

        if(!str_starts_with($private_key_mm, '0x'))
            $private_key_mm = '0x' . $private_key_mm;

        $config_data = array("sender"=>$sender,
                             "private_key"=>$private_key,
                             "private_key_mm"=>$private_key_mm,
                             "fee_token"=>(int)$fee_token);

        $config_json = json_encode($config_data, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents($config_file, $config_json);

        Redirect('/transfer/finish', false);
    }

?>