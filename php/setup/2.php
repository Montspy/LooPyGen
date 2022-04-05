<?php

    $collection_lower = file_get_contents(".tempfile");
    $traits_file = file_get_contents("./images/${collection_lower}/traits.json");
    $traits = json_decode($traits_file, true);
    $s = 1;
    $t_display = $traits['trait_count'];

    if (!empty($traits) and $redirect !== "TRUE") { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <div class="section">
                <p>STEP 02 - Define trait names and how many variations each will have.</p>
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
        <h3>Setup your Traits</h3>
        <form method="post" action="/setup/2">
            <?php $i = 0; while ($i <= $traits['trait_count']) {
                if ($traits['background_color'] === true and $i == 0) { ?>
                    <h4>Setup Background Color Trait:</h4>
                    <div class="trait-row">
                        <div data-tooltip="Display Name: The pretty name of this trait/layer"><input required type="text" class="form med" id="trait<?php echo $s ?>_name" name="trait<?php echo $s ?>_name" placeholder="Background Display Name" /></div>
                        <div class="labeled" data-tooltip="Colors Count: The number of possible background colors">
                            <label for="trait<?php echo $s ?>_vars">
                                How many variations?
                            </label>
                            <input required type="number" class="form number" id="trait<?php echo $s ?>_vars" min="1" name="trait<?php echo $s ?>_vars" placeholder="1" />
                        </div>
                    </div>
                    <div class="trait-row">
                        <label>
                            Size of your images:
                        </label>
                        <div class="labeled" data-tooltip="Image Size: The dimensions in pixels of your images [height: optional]">
                            <input required type="number" class="form size" id="trait<?php echo $s ?>_x" min="1" name="trait<?php echo $s ?>_x" placeholder="WIDTH" />x
                            <input required type="number" class="form size" id="trait<?php echo $s ?>_y" min="1" name="trait<?php echo $s ?>_y" placeholder="HEIGHT" />
                        </div>
                    </div>
                <?php } else { ?>
                    <h4>Setup Trait #<?php echo $s ?>:</h4>
                    <div class="trait-row">
                        <div data-tooltip="Display Name: The pretty name of this trait/layer"><input required type="text" class="form med" id="trait<?php echo $s ?>_name" name="trait<?php echo $s ?>_name" placeholder="Trait #<?php echo $s ?> Display Name" /></div>
                        <div class="labeled" data-tooltip="Variations Count: The number of possible values for this trait/layer">
                            <label for="trait<?php echo $s ?>_vars">
                                How many variations?
                            </label>
                            <input required type="number" class="form number" id="trait<?php echo $s ?>_vars" min="1" name="trait<?php echo $s ?>_vars" placeholder="1" />
                        </div>
                    </div>
            <?php } $i = $i + 1; $s = $s + 1; } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 03" />
        </form>
    <?php } else if (!empty($traits) and $redirect === "TRUE") {
        $i = 0;
        if ($traits['background_color'] === true) { $s = 0; } else { $s = 1; }
        $traits["image_layers"] = array();
        while ($i <= $traits['trait_count']) {
            $traits["image_layers"][$i]["variations"] = (int)$_POST["trait${s}_vars"];
            $traits["image_layers"][$i]["layer_name"] = $_POST["trait${s}_name"];
            if ($traits['background_color'] === true and $i == 0) {
                $traits["image_layers"][$i]["size"] = array((int)$_POST["trait${s}_x"], (int)$_POST["trait${s}_y"]);
            }
            $i = $i + 1;
            $s = $s + 1;
        }
        $traits_json = json_encode($traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./images/${collection_lower}/traits.json", $traits_json);
        Redirect('/setup/3', false);
    } else {
        Redirect('/setup/1', false);
    }

?>