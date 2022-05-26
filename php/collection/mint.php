<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    if (!file_exists("./config.json")) {
        Redirect("/config/1");
    }

    echo '<h1>Mint Collection</h1>';

    if (empty($_GET['collection'])) {
        echo '<h3>Choose a collection:</h3>';
        $found = 0;
        foreach ($collections as $c) {
            if ($c !== ".keep") {
                $cf = "./collections/${c}/config/traits.json";
                if (file_exists($cf)) {
                    $ctf = file_get_contents($cf);
                    $ct = json_decode($ctf, true);
                    $lower = $ct['collection_lower'];
                    $name = $ct['collection_name'];
                    echo "<a href=\"/collection/mint?collection=${lower}\"><button class=\"btn\">${name}</button></a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1"><button class="btn">CREATE NEW COLLECTION</button></a>';
        }
    } else if (empty($_GET['run'])) {
        $lower = $_GET['collection']; ?>
        <form method="post" action="/collection/mint?collection=<?php echo $lower; ?>">
            <h3>Minter Options</h3>
            <h3 class="warning">You will not receive estimated fees, this runs the commands with current prices.</h3>
            <div id="artist" class="section">
                <div class="row">
                    <div data-tooltip="Copies: (Required) How many copies of each NFT should be minted?">
                        <label for="amount">
                            How many copies?
                        </label>
                        <input required type="number" class="form small" id="amount" name="amount" />
                    </div>
                    <div data-tooltip="Start ID: (Optional) Choose a token ID to start with.">
                        <label for="start_id">
                            Start ID:
                        </label>
                        <input type="number" class="form small" id="start_id" name="start_id" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="End ID: (Optional) Choose a token ID to end with.">
                        <label for="end_id">
                            End ID:
                        </label>
                        <input type="number" class="form small" id="end_id" name="end_id" />
                    </div>
                    <div data-tooltip="Test: (Recommended) Run a test mint, but don't actually mint anything.">
                        <label for="testmint">
                            Run as a test?
                        </label>
                        <input type="checkbox" class="form small" id="testmint" name="testmint" />
                    </div>
                </div>
            </div>
            <input class="form btn" type="submit" name="submit" value="NEXT STEP" />
        </form>
    <?php } else if (!empty($_POST['amount'])) {
        $lower = $_GET['collection'];
        $amount = $_POST['amount'];
        if (!empty($_POST['start_id'])) { $start_id = "--start " . $_POST['start_id']; } else { $start_id = ""; }
        if (!empty($_POST['end_id'])) { $end_id = "--end " . $_POST['end_id']; } else { $end_id = ""; }
        if (!empty($_POST['testmint'])) { $testmint = "--testmint"; } else { $testmint = "--testmint"; }
        $command = "mint --noprompt --amount ${amount} --name ${lower} ${start_id} ${end_id} ${testmint}"; ?>
        <h3 class="success">Confirm mint. This might take a while.</h3>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <p><code>Command: <?php echo $command; ?></code></p>
        <form method="post" action="/collection/mint?collection=<?php echo $lower; ?>&run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <input class="form btn" type="submit" name="submit" value="MINT" />
        </form>
    <?php } else if (!empty($_GET['run'])) {
        $lower = $_GET['collection'];
        $command = $_POST['command'];
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

?>