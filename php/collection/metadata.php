<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    echo '<h1>Metadata Generation</h1>';

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
                    echo "<a href=\"/collection/metadata?collection=${lower}\"><button class=\"btn\">${name}</button></a>";
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
        <form method="post" action="/collection/metadata?collection=<?php echo $lower; ?>&run=true">
            <h3>Generate Metadata. This might take a while.</h3>
            <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
            <div id="artist" class="section">
                <div class="row">
                    <div data-tooltip="Empty: (Optional) Delete any previously generated metadata and start fresh.">
                        <label for="empty">
                            Empty old metadata?
                        </label>
                        <input type="checkbox" id="empty" name="empty" />
                    </div>
                    <div data-tooltip="Overwrite: (Optional) Overwrite existing metadata files with new trait information.">
                        <label for="overwrite">
                            Overwrite metadata?
                        </label>
                        <input type="checkbox" id="overwrite" name="overwrite" />
                    </div>
                </div>
            </div>
            <input class="form btn" type="submit" name="submit" value="GENERATE" />
        </form>
    <?php } else if (!empty($_GET['run'])) {
        $lower = $_GET['collection'];
        if (!empty($_POST['empty'])) { $empty = "--empty"; } else { $empty = ""; }
        if (!empty($_POST['overwrite'])) { $overwrite = "--overwrite"; } else { $overwrite = ""; }
        $command = "metadata --name ${lower} ${empty} ${overwrite}"; ?>
        <h3 class="success">Metadata Generation Done!</h3>
        <?php exec($command, $output, $code);
        if ($code == 0) {
            $code = "Success!";
        } else {
            $code = "Error: ${code} (see output below)";
        } ?>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    echo $line . "<br />";
} ?>
<br /><br />
<?php exec("ls -n ./collections/${lower}/ipfs/metadata", $list, $code);
foreach ($list as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <a href="javascript:window.history.back();"><button class="btn">GO BACK</button></a>
        <a href="/collection/mint?collection=<?php echo $lower; ?>"><button class="btn">MINT</button></a>
        <a href="/home"><button class="btn">MAIN MENU</button></a>
    <?php }

?>