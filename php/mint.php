<?php

    if (!file_exists("./config.json")) {
        Redirect("/config/1");
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

    echo '<div class="section">';
    echo '<h1>Mint Single NFT</h1>';

    if (empty($_GET['run'])) { ?>
        <form method="post" action="/mint?run=true">
            <h3>Minter Options</h3>
            <h3 class="warning">You will not receive estimated fees, this runs the commands with current prices.</h3>
            <h3>Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
            <div id="artist" class="section">
                <div data-tooltip="CID: (Required) Paste your metadata file's CID from Pinata.">
                    <label for="cid">
                        CID:
                    </label>
                    <input required type="text" pattern="^Qm[a-zA-Z0-9]{44}$" class="form wide" id="cid" name="cid" />
                </div>
                <div class="row">
                    <div data-tooltip="Copies: (Required) How many copies of the NFT should be minted?">
                        <label for="amount">
                            Copies:
                        </label>
                        <input required type="number" class="form small" id="amount" name="amount" />
                    </div>
                    <div data-tooltip="Test: (Recommended) Run a test mint, but don't actually mint anything.">
                        <label for="testmint">
                            Run as a test?
                        </label>
                        <input type="checkbox" id="testmint" name="testmint" />
                    </div>
                </div>
            </div>
            <input class="form btn" type="submit" name="submit" value="MINT IT" />
        </form>
    <?php } else if (!empty($_POST['cid'])) {
        $amount = $_POST['amount'];
        $cid = $_POST['cid'];
        if (!empty($_POST['testmint'])) { $testmint = "--testmint"; } else { $testmint = ""; }
        $command = "mint --noprompt --amount ${amount} --cid ${cid} ${testmint}";
        exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
        } else {
            $code = "Error: ${code} (see output below)";
        } ?>
        <h3 class="success">Minting Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <a href="/home"><button class="btn">MAIN MENU</button></a>
    <?php }

    echo '</div>';

?>