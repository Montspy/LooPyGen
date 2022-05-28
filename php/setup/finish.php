<?php

    $collection_lower = $_GET['collection'];
    $traits_file = file_get_contents("./collections/${collection_lower}/config/traits.json");
    $traits = json_decode($traits_file, true);
    $s = 1;
    $t_display = $traits['trait_count'];

    if (!empty($traits)) { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <div class="section">
                <p><b>Collection Name</b>: <?php echo $traits['collection_name'] ?></p>
                <?php if (array_key_exists('artist_name', $traits)) {
                    echo "<p><b>Artist's Name</b>: " . $traits['artist_name'] . "</p>";
                } ?>
                <?php if (array_key_exists('royalty_address', $traits)) {
                    echo "<p><b>Royalty Address</b>: " . $traits['royalty_address'] . "</p>";
                } ?>
                <?php if ($traits['background_color'] === true) {
                    echo "<p><b>Generate Background Colors</b>: YES</p>";
                    $s = 0;
                    $t_display = $t_display + 1;
                } ?>
                <p><b>Total Traits</b>: <?php echo $t_display ?></p>
            </div>
        </div>
        <a href="/collection/images?collection=<?php echo $collection_lower ?>"><button class="btn">GENERATE IMAGES</button></a>
        <a href="/home"><button class="btn">MAIN MENU</button></a>
    <?php } else {
        Redirect('/setup/1', false);
    }

?>