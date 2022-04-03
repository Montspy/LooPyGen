<?php

    $collection_lower = file_get_contents(".tempfile");
    $traits_file = file_get_contents("./images/${collection_lower}/traits.json");
    $traits = json_decode($traits_file, true);

    if (!empty($traits) and $redirect !== "TRUE") { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <div class="section">
                <p><b>Collection Name</b>: <?php echo $traits['collection_name'] ?></p>
                <p><b>Artist</b>: <?php echo $traits['artist_name'] ?></p>
                <?php if (array_key_exists('artist_address', $traits)) {
                    echo "<p><b>Artist's Address</b>: " . $traits['artist_address'] . "</p>";
                } ?>
                <p><b>Minter's Address</b>: <?php echo $traits['mint_address'] ?></p>
                <p><b>Traits</b>: <?php echo $traits['trait_count'] ?></p>
                <?php if ($traits['background_color'] == 0) {
                    echo "<p><b>Generate Background Colors</b>: YES</p>";
                } ?>
            </div>
        </div>
        <h3>Setup your Traits</h3>
        <form method="post" action="/2">
            <?php $i = 0; while ($i <= $traits['trait_count']) {
                if ($traits['background_color'] === true and $i == 0) { ?>
                    <h4>Setup Background Color Trait:</h4>
                    <div class="trait-row">
                        <input required type="text" class="form med" id="trait<?php echo $i ?>_name" name="trait<?php echo $i ?>_name" placeholder="Background Display Name" />
                        <div class="labeled">
                            <label for="trait<?php echo $i ?>_vars">
                                How many colors will the background have?
                            </label>
                            <input required type="number" class="form number" id="trait<?php echo $i ?>_vars" min="1" name="trait<?php echo $i ?>_vars" placeholder="1" />
                        </div>
                    </div>
                    <div class="trait-row">
                        <label>
                            Size of your images:
                        </label>
                        <div class="labeled">
                            <input required type="number" class="form size" id="trait<?php echo $i ?>_x" min="1" name="trait<?php echo $i ?>_x" placeholder="WIDTH" />x
                            <input required type="number" class="form size" id="trait<?php echo $i ?>_y" min="1" name="trait<?php echo $i ?>_y" placeholder="HEIGHT" />
                        </div>
                    </div>
                <?php } else { ?>
                    <h4>Setup Trait #<?php echo $i ?>:</h4>
                    <div class="trait-row">
                        <input required type="text" class="form med" id="trait<?php echo $i ?>_name" name="trait<?php echo $i ?>_name" placeholder="Trait #<?php echo $i ?> Display Name" />
                        <label for="trait<?php echo $i ?>_vars">
                            How many variations?
                        </label>
                        <input required type="number" class="form number" id="trait<?php echo $i ?>_vars" min="1" name="trait<?php echo $i ?>_vars" placeholder="1" />
                    </div>
            <?php } $i = $i + 1; } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 03" />
        </form>
    <?php } else if (!empty($traits) and $redirect === "TRUE") {
        $i = 0;
        $traits["image_layers"] = array();
        while ($i <= $traits['trait_count']) {
            $traits["image_layers"][$i]["variations"] = (int)$_POST["trait${i}_vars"];
            $traits["image_layers"][$i]["layer_name"] = $_POST["trait${i}_name"];
            if ($traits['background_color'] === true and $i == 0) {
                $traits["image_layers"][$i]["size"] = array((int)$_POST["trait${i}_x"], (int)$_POST["trait${i}_y"]);
            }
            $i = $i + 1;
        }
        $traits_json = json_encode($traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./images/${collection_lower}/traits.json", $traits_json);
        Redirect('/3', false);
    } else {
        Redirect('/1', false);
    }
?>