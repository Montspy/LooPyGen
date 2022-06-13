<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    echo '<section>';
    echo '<h1>Image Generation</h1>';

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
                    echo "<a href=\"/collection/images?collection=${lower}\">${name}</a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1">CREATE NEW COLLECTION</a>';
        }
        echo '</div>';
    } else if (empty($_POST)) {
        $lower = $_GET['collection']; ?>
        <form method="post" action="/collection/images?collection=<?php echo $lower; ?>">
            <h3>Generator Options</h3>
            <section id="artist">
                <div class="row">
                    <div data-tooltip="Count: (Required) How many unique images do you want to generate?">
                        <label for="count">
                            How many?
                        </label>
                        <input required type="number" class="form small" id="count" name="count" />
                    </div>
                    <div data-tooltip="Start ID: (Optional) Choose a token ID to start with.">
                        <label for="start_id">
                            Start ID:
                        </label>
                        <input type="number" class="form small" id="start_id" name="start_id" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Empty: (Optional) Delete any previously generated images and start fresh.">
                        <label for="empty">
                            Empty old images?
                        </label>
                        <input type="checkbox" id="empty" name="empty" />
                    </div>
                    <div data-tooltip="Threaded: (Optional) Compile 4 images at a time. ONLY USE IF YOU HAVE A POWERFUL COMPUTER!">
                        <label for="threaded">
                            Multi-threaded?
                        </label>
                        <input type="checkbox" id="threaded" name="threaded" />
                    </div>
                </div>
            </div>
            <input class="form btn" type="submit" name="submit" value="NEXT STEP" />
        </form>
    <?php } else if (!empty($_POST['count'])) {
        $lower = $_GET['collection'];
        $count = $_POST['count'];
        if (!empty($_POST['start_id'])) { $start_id = "--id " . $_POST['start_id']; } else { $start_id = ""; }
        if (!empty($_POST['empty'])) { $empty = "--empty"; } else { $empty = ""; }
        if (!empty($_POST['threaded'])) { $threaded = "--threaded"; } else { $threaded = ""; }
        $command = "generate --count ${count} --name ${lower} ${start_id} ${empty} ${threaded} 2>&1"; ?>
        <h3 class="success">Confirm image generation. This might take a while.</h3>
        <h3 class="warning">DO NOT CLOSE OR REFRESH THIS WINDOW/TAB</h3>
        <p><code>Command: <?php echo $command; ?></code></p>
        <form method="post" action="/collection/images?collection=<?php echo $lower; ?>&run=true">
            <input type="hidden" id="command" name="command" value="<?php echo $command; ?>" />
            <input onclick="openModal('loading')" class="form btn" type="submit" name="submit" value="GENERATE" />
        </form>
        <div class="modal" id="loading">
            <h2>Hang tight, we're generating <?php echo $count; ?> images for you...</h2>
            <div class="modal-content">
                <img loading="lazy" src="/css/images/generate.gif" alt="GENERATING IMAGES..." />
            </div>
        </div>
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
        <h3 class="<?php echo $type; ?>">Image Generation Done!</h3>
        <pre>
Result: <?php echo $code; ?>
<br /><br />
<?php foreach ($output as $line) {
    if (strstr($line, "Generating") !== false) {
        continue;
    } else {
        echo $line . "<br />";
    }
} ?>
<br /><br />
<?php exec("ls -n ./collections/${lower}/ipfs/images", $list, $code);
foreach ($list as $line) {
    echo $line . "<br />";
} ?>
        </pre>
        <div class="nav">
            <a href="javascript:window.history.back();">GO BACK</a>
            <a href="/collection/metadata?collection=<?php echo $lower; ?>">METADATA</a>
            <a href="/home">MAIN MENU</a>
        </div>
    <?php }

    echo '</section>';

?>