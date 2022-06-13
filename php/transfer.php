<?php

    if (!file_exists($transfer_config)) {
        BrowserRedirect("/transfer-config/1");
    }

    $infuraUrl = "https://mainnet.infura.io/v3/3b6a7ab1f65746d18cb72e4e216b55cb";
    $json = '{"jsonrpc":"2.0","method":"eth_gasPrice","params": [],"id":1}';
    $curl = curl_init();
    curl_setopt($curl, CURLOPT_URL, $infuraUrl);
    curl_setopt($curl, CURLOPT_POST, true);
    curl_setopt($curl, CURLOPT_POSTFIELDS, $json);
    curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
    $response = curl_exec($curl);
    curl_close($curl);
    $results = json_decode($response, true);
    $gas = hexdec($results['result']) / 1000000000;

    echo '<section>';
    echo '<h1>Transfer any NFTs</h1>';

    if (empty($_GET['run']) and (empty($_POST['wallets']) or empty($_POST['nfts']) or empty($_POST['mode']))) { ?>
        <form method="post" action="/transfer">
            <h3 class="warning">You will not receive estimated fees, this runs the commands with current prices.</h3>
            <h3 class="info">Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
            <h3>Transfer Options</h3>
            <section id="artist">
                <div class="row">
                    <div data-tooltip="List of L2 addresses or ENS to send to, one per line.">
                        <label for="wallets">
                            Wallets:
                        </label>
                        <textarea required class="form wide" id="wallets" name="wallets"></textarea>
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="List of CIDs or NFT IDs to send.&#xa;Random: At least as many NFTs as wallets must be in the sender wallet, including copies&#xa;Ordered: List the same number of NFTs as wallets">
                        <label for="nfts">
                            NFTs:
                        </label>
                        <textarea required class="form wide" id="nfts" name="nfts"></textarea>
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Random: Each wallet will receive a random NFT from the list&#xa;Ordered: One-to-one association between wallet and NFT. The 1st wallet will receive the 1st NFT in the list, The 2nd wallet the 2nd NFT, etc...">
                        <label for="mode">
                            Tranfer mode
                        </label>
                        <select required class="form med" id="mode" name="mode">
                            <option selected value="--random">Random</option>
                            <option value="--ordered">Ordered</option>
                        </select>
                    </div>
                    <div data-tooltip="Test: (Recommended) Run a test, but don't actually transfer anything.">
                        <label for="test">
                            Run as a test?
                        </label>
                        <input checked type="checkbox" id="test" name="test" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="The passphrase to your transfer config file">
                        <label for="configpass">
                            Transfer config passphrase
                        </label>
                        <input type="password" class="form med" id="configpass" name="configpass" />
                    </div>
                </div>
            </section>
            <button class="form btn" name="submit">TRANSFER</button>
        </form>
    <?php } else if (empty($_GET['run'])) {
        // Build command from inputs
        $wallet_file = "/tmp/wallets.txt";
        $nft_file = "/tmp/nfts.txt";
        $wallets = $_POST['wallets'];
        $nfts = $_POST['nfts'];
        $mode = $_POST['mode'];
        if (!empty($_POST['test'])) { $test = "--test"; } else { $test = ""; }
        if (!empty($_POST['configpass'])) { $configpass = "--configpass " . base64_encode($_POST['configpass']); } else { $configpass = ""; }
        $fees_command = "transfer --php --noprompt --nfts ${nft_file} --to ${wallet_file} ${mode} ${test} ${configpass} --fees 2>&1";
        $command = str_replace("--fees", "", $fees_command);
        file_put_contents($wallet_file, $wallets);
        file_put_contents($nft_file, $nfts);

        // Get estimated fees
        exec($fees_command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
            $matches = preg_grep('/^Estimated L2 fees/', $output);
            $estimated_fees = end($matches);
            $printable_output = '<h3 class="info">' . $estimated_fees . '</h3>';
        } else {
            $code = "Error: ${code} (see output below)";
            $printable_output = '<pre class="error">Error estimating fees:<br /><br />';
            foreach ($output as $line) {
                $printable_output .= $line . '<br />';
            }
            $printable_output .= '</pre>';
        }
        ?>
        <h3 class="success">Confirm transfer. This might take a while.</h3>
        <?php
            echo $printable_output;
            if (strpos($command, "--testmint") !== false) {
                echo "<h3 class='info'>Test Mode enabled. Fees will not be paid.</h3>";
            } else {
                echo "<h3 class='warning'>Transfers are active. Fees will be paid.</h3>";
            }
        ?>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <form method="post" action="/transfer?run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <button class="form btn" type="submit" name="submit">TRANSFER</button>
        </form>
    <?php } else if (!empty($_GET['run'])) {
        $wallet_file = "/tmp/wallets.txt";
        $nft_file = "/tmp/nfts.txt";
        $command = $_POST['command'];
        exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
        } else {
            $code = "Error: ${code} (see output below)";
        }

        if (file_exists($wallet_file)) {
            unlink($wallet_file);
        }
        if (file_exists($nft_file)) {
            unlink($nft_file);
        } ?>
        <h3 class="success">Transfer Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <div class="nav"><a href="/home">MAIN MENU</a></div>
    <?php }

    echo '</section>';

?>