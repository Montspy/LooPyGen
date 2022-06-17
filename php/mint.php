<?php

    if (!file_exists($mint_config)) {
        BrowserRedirect("/mint-config/1");
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
    echo '<h1>Mint Single NFT</h1>';

    if (empty($_GET['run']) and (empty($_POST['cid']) or empty($_POST['amount']))) { ?>
        <form method="post" action="/mint">
            <h3 class="warning">You will not receive estimated fees, this runs the commands with current prices.</h3>
            <h3 class="info">Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
            <h3>Minter Options</h3>
            <section id="artist">
                <div data-tooltip="CID: The metadata file's IPFS CID&#xa;[required]">
                    <label for="cid">
                        CID:
                    </label>
                    <input required type="text" pattern="^Qm[a-zA-Z0-9]{44}$" class="form wide" id="cid" name="cid" />
                </div>
                <div class="row">
                    <div data-tooltip="Copies: The number of copies to mint&#xa;[required]">
                        <label for="amount">
                            Copies:
                        </label>
                        <input required type="number" class="form small" id="amount" name="amount" />
                    </div>
                    <div data-tooltip="Test: (Recommended) Run a test mint, but don't actually mint anything.">
                        <label for="testmint">
                            Run as a test?
                        </label>
                        <input checked type="checkbox" id="testmint" name="testmint" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="The passphrase to your mint config file&#xa;[required]">
                        <label for="configpass">
                            Mint config passphrase
                        </label>
                        <input type="password" class="form med" id="configpass" name="configpass" />
                    </div>
                </div>
            </section>
            <button onclick="openModal('loading-fees')" class="form btn" name="submit">REVIEW MINT</button>
        </form>
        <div class="modal" id="loading-fees">
            <div class="modal-content">
                <h2>Retrieving estimated fees...</h2>
                <img loading="lazy" src="/css/images/fees.gif" alt="GETTING FEES..." />
                <h4 style="display: none;"><span id="loading-fees-progress"></span><span id="loading-fees-progress--spinner"></span></h4>
            </div>
        </div>
    <?php } else if (empty($_GET['run'])) {
        // Build command from inputs
        $cid = $_POST['cid'];
        $amount = $_POST['amount'];
        if (!empty($_POST['testmint'])) { $testmint = "--testmint"; } else { $testmint = ""; }
        if (!empty($_POST['configpass'])) { $configpass = "--configpass " . base64_encode($_POST['configpass']); } else { $configpass = ""; }
        $fees_command = "mint --php --noprompt --amount ${amount} --cid ${cid} ${testmint} ${configpass} --fees 2>&1";
        $command = str_replace("--fees", "", $fees_command);

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
        <h3 class="success">Confirm mint. This might take a while.</h3>
        <?php
            echo $printable_output;
            if (strpos($command, "--testmint") !== false) {
                echo "<h3 class='info'>Test Mode enabled. Fees will not be paid.</h3>";
                $loading_msg = "Hang tight, we're test minting your NFT...";
            } else {
                echo "<h3 class='warning'>Minting is active. Fees will be paid.</h3>";
                $loading_msg = "Hang tight, we're minting your NFT...";
            }
        ?>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <form method="post" action="/mint?run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <button onclick="openModal('loading')" class="form btn" type="submit" name="submit">MINT IT</button>
        </form>
        <div class="modal" id="loading">
            <div class="modal-content">
                <h2><?php echo $loading_msg; ?></h2>
                <img loading="lazy" src="/css/images/minting.gif" alt="MINTING..." />
                <h4><span id="loading-progress"></span><span id="loading-progress--spinner"></span></h4>
            </div>
        </div>
    <?php } else if (!empty($_GET['run'])) {
        $command = $_POST['command'];
        exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
        } else {
            $code = "Error: ${code} (see output below)";
        }
        
        if (file_exists($progress_file)) {
            unlink($progress_file);
        } ?>
        <h3 class="success">Minting Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <div class="nav">
            <a href="/mint">MINT AGAIN</a>
            <a href="/home">MAIN MENU</a>
        </div>
    <?php }

    echo '</section>';

?>