<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

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

    echo '<section>';
    echo '<h1>Mint Collection</h1>';

    if (empty($_GET['collection'])) {
        echo '<h3>Choose a collection:</h3>';
        echo '<div class="nav">';
        $found = 0;
        foreach ($collections as $c) {
            if ($c !== ".keep") {
                $cf = "./collections/${c}/config/traits.json";
                if (file_exists($cf)) {
                    $ctf = file_get_contents($cf);
                    $ct = json_decode($ctf, true);
                    $lower = $ct['collection_lower'];
                    $name = $ct['collection_name'];
                    echo "<a href=\"/collection/mint?collection=${lower}\">${name}</a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1">CREATE NEW COLLECTION</a>';
        }
        echo '</div>';
    } else if (empty($_GET['run']) and (empty($_POST['amount']))) {
        $lower = $_GET['collection']; ?>
        <form method="post" action="/collection/mint?collection=<?php echo $lower; ?>">
            <h3 class="warning">You will receive estimated fees in the review screen</h3>
            <h3 class="info">Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
            <h3>Minter Options</h3>
            <section id="artist">
                <div class="row">
                    <div data-tooltip="Start ID: (Optional) Choose a token ID to start with.">
                        <label for="start_id">
                            Start ID:
                        </label>
                        <input type="number" class="form small" id="start_id" name="start_id" />
                    </div>
                    <div data-tooltip="End ID: (Optional) Choose a token ID to end with.">
                        <label for="end_id">
                            End ID:
                        </label>
                        <input type="number" class="form small" id="end_id" name="end_id" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Copies: (Required) How many copies of each NFT should be minted?">
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
                    <div data-tooltip="The passphrase to your mint config file">
                        <label for="configpass">
                            Mint config passphrase:
                        </label>
                        <input type="password" class="form med" id="configpass" name="configpass" />
                    </div>
                </div>
            </section>
            <button class="form btn" name="submit">REVIEW MINT</button>
        </form>
    <?php } else if (empty($_GET['run'])) {
        // Build command from inputs
        $lower = $_GET['collection'];
        $amount = $_POST['amount'];
        if (!empty($_POST['start_id'])) { $start_id = "--start " . $_POST['start_id']; } else { $start_id = ""; }
        if (!empty($_POST['end_id'])) { $end_id = "--end " . $_POST['end_id']; } else { $end_id = ""; }
        if (!empty($_POST['testmint'])) { $testmint = "--testmint"; } else { $testmint = ""; }
        if (!empty($_POST['configpass'])) { $configpass = "--configpass " . base64_encode($_POST['configpass']); } else { $configpass = ""; }
        $fees_command = "mint --php --noprompt --amount ${amount} --name ${lower} ${start_id} ${end_id} ${testmint} ${configpass} --fees 2>&1";
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
            $printable_output = '<pre class="error">Error:<br /><br />';
            foreach ($output as $line) {
                $printable_output .= $line . '<br />';
            }
            $printable_output .= '</pre>';
        }
        ?>
        <h3 class="success">Confirm mint. This might take a while.</h3>
        <?php echo $printable_output ?>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <p><code>Command: <?php echo $command; ?></code></p>
        <form method="post" action="/collection/mint?collection=<?php echo $lower; ?>&run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <button class="form btn" type="submit" name="submit">MINT</button>
        </form>
    <?php } else if (!empty($_GET['run'])) {
        $lower = $_GET['collection'];
        $command = $_POST['command'];
        exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
            $type = "success";
        } else {
            $code = "Error: ${code} (see output below)";
            $type = "error";
        } ?>
        <h3 class="<?php echo $type; ?>">Minting Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <div class="nav">
            <a href="javascript:window.history.back();">GO BACK</a>
            <a href="/collection/mint?collection=<?php echo $lower; ?>">MINT</a>
            <a href="/home">MAIN MENU</a>
        </div>
    <?php }

    echo '</section>';

?>