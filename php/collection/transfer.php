<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    if (!file_exists("./transfer_config.json")) {
        Redirect("/transfer-config/1");
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
    echo '<h1>Transfer Collection</h1>';

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
                    echo "<a href=\"/collection/transfer?collection=${lower}\">${name}</a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1">CREATE NEW COLLECTION</a>';
        }
        echo '</div>';
    } else if (empty($_GET['run']) and (empty($_POST['wallets']) or empty($_POST['mode']))) {
        $lower = $_GET['collection']; ?>
        <form method="post" action="/collection/transfer?collection=<?php echo $lower; ?>">
            <h3 class="warning">You will receive estimated fees in the review screen</h3>
            <h3 class="info">Current Gas: <?php echo number_format((float)$gas, 2, '.', ''); ?> Gwei</h3>
            <h3>Transfer Options</h3>
            <section>
                <div class="row">
                    <div data-tooltip="Wallets: The L2 addresses or ENS to send to, one per line.">
                        <label for="wallets">
                            Wallets:
                        </label>
                        <textarea required class="form wide" id="wallets" name="wallets"></textarea>
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Tranfer mode: Send the NFTs ordered by ID or in a random order.">
                        <label for="mode">
                            Tranfer mode
                        </label>
                        <select required class="form med" id="mode" name="mode">
                            <option selected value="--random">Random</option>
                            <option value="--ordered">Ordered (by ID)</option>
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
            <button class="form btn" name="submit">REVIEW TRANSFER</button>
        </form>
    <?php } else if (empty($_GET['run'])) {
        // Build command from inputs
        $lower = $_GET['collection'];
        $wallet_file = "/tmp/wallets.txt";
        $wallets = $_POST['wallets'];
        $mode = $_POST['mode'];
        if (!empty($_POST['test'])) { $test = "--test"; } else { $test = ""; }
        if (!empty($_POST['configpass'])) { $configpass = "--configpass " . base64_encode($_POST['configpass']); } else { $configpass = ""; }
        $fees_command = "transfer --php --noprompt --nfts ${lower} --to ${wallet_file} ${mode} ${test} ${configpass} --fees 2>&1";
        $command = str_replace("--fees", "", $fees_command);
        file_put_contents($wallet_file, $wallets);

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
        <h3 class="success">Confirm transfer. This might take a while.</h3>
        <?php echo $printable_output ?>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <p><code>Command: <?php echo $command; ?></code></p>
        <form method="post" action="/collection/transfer?collection=<?php echo $lower; ?>&run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <button class="form btn" type="submit" name="submit">TRANSFER</button>
        </form>
    <?php
    } else if (!empty($_GET['run'])) {
        $wallet_file = "/tmp/wallets.txt";
        $lower = $_GET['collection'];
        $command = $_POST['command'];
        exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
            $type = "success";
        } else {
            $code = "Error: ${code} (see output below)";
            $type = "error";
        }
        if (file_exists($wallet_file)) {
            unlink($wallet_file);
        }
        ?>
        <h3 class="<?php echo $type; ?>">Transfers Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <div class="nav">
            <a href="javascript:window.history.back();">GO BACK</a>
            <a href="/home">MAIN MENU</a>
        </div>
    <?php }

    echo '</section>';

?>