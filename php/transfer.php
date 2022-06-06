<?php

    if (!file_exists("./transfer_config.json")) {
        Redirect("/transfer/1");
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

    if (empty($_GET['run'])) { ?>
        <form method="post" action="/transfer?run=true">
            <h3>Transfer Options</h3>
            <h3 class="warning">You will not receive estimated fees, this runs the commands with current prices.</h3>
            <h3>Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
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
            </section>
            <button class="form btn" name="submit">TRANSFER</button>
        </form>
    <?php } else if (!empty($_POST['wallets'])) {
        $wallet_file = "/tmp/wallets.txt";
        $nft_file = "/tmp/nfts.txt";
        $wallets = $_POST['wallets'];
        $nfts = $_POST['nfts'];
        $mode = $_POST['mode'];
        if (!empty($_POST['test'])) { $test = "--test"; } else { $test = ""; }
        $command = "transfer --noprompt --nfts ${nft_file} --to ${wallet_file} ${mode} ${test}";
        echo $command;
        file_put_contents($wallet_file, $wallets);
        file_put_contents($nft_file, $nfts);
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