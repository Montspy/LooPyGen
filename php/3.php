<?php

    $collection_lower = file_get_contents(".tempfile");
    $traits_file = file_get_contents("./images/${collection_lower}/traits.json");
    $traits = json_decode($traits_file, true);

    if (!empty($traits) and $redirect !== "TRUE") { ?>
        <h2>Collection Info</h2>
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
        <form method="post" action="/3">
            <?php $t = 0;
            while ($t <= $traits['trait_count']) {
                if ($t == 0 and $traits['background_color'] === true) { ?>
                    <h3 class="trait-title">Setup Background Colors:</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $t . "_" . $v; ?>
                        <h4>Color #<?php echo $v ?>:</h4>
                        <div class="trait-row">
                            <input required type="text" class="form med" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Variation Name" />
                            <label for="trait<?php echo $trait_var ?>_weight">Set Rarity:&nbsp;&nbsp;</label>
                            <select required class="form med" id="trait<?php echo $trait_var ?>_weight" name="trait<?php echo $trait_var ?>_weight">
                                <option value="1">Legendary</option>
                                <option value="2">Rare</option>
                                <option value="3">Uncommon</option>
                                <option value="4">Common</option>
                            </select>
                        </div>
                        <div class="trait-row">
                            <label for="trait<?php echo $trait_var ?>_r">Red:&nbsp;&nbsp;</label>
                            <input required type="number" class="form number" id="trait<?php echo $trait_var ?>_r" min="0" max="255" name="trait<?php echo $trait_var ?>_r" placeholder="0-255" />
                            <label for="trait<?php echo $trait_var ?>_g">Green:&nbsp;&nbsp;</label>
                            <input required type="number" class="form number" id="trait<?php echo $trait_var ?>_g" min="0" max="255" name="trait<?php echo $trait_var ?>_g" placeholder="0-255" />
                            <label for="trait<?php echo $trait_var ?>_b">Blue:&nbsp;&nbsp;</label>
                            <input required type="number" class="form number" id="trait<?php echo $trait_var ?>_b" min="0" max="255" name="trait<?php echo $trait_var ?>_b" placeholder="0-255" />
                            <label for="trait<?php echo $trait_var ?>_a">Opacity:&nbsp;&nbsp;</label>
                            <input required type="number" class="form number" id="trait<?php echo $trait_var ?>_a" min="0" max="255" name="trait<?php echo $trait_var ?>_a" placeholder="0-255" />
                        </div>
                    <?php $v = $v + 1; }
                } else { ?>
                    <h3 class="trait-title">Setup "<?php echo $traits['image_layers'][$t]['layer_name'] ?>" Trait:</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $t . "_" . $v; ?>
                        <h4>Variation #<?php echo $v ?>:</h4>
                        <div class="trait-row">
                            <input required type="text" class="form med" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Variation Name" />
                            <label for="trait<?php echo $trait_var ?>_weight">Set Rarity:&nbsp;&nbsp;</label>
                            <select required class="form med" id="trait<?php echo $trait_var ?>_weight" name="trait<?php echo $trait_var ?>_weight">
                                <option value="1">Legendary</option>
                                <option value="2">Rare</option>
                                <option value="3">Uncommon</option>
                                <option value="4">Common</option>
                            </select>
                        </div>
                        <div class="trait-row">
                            <label for="trait<?php echo $trait_var ?>_r">Filename:</label>
                            <input required type="text" class="form med" id="trait<?php echo $trait_var ?>_file" name="trait<?php echo $trait_var ?>_file" placeholder="variation_file_name.png" />
                        </div>
                    <?php $v = $v + 1; }
                }
                $t = $t + 1;
            } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 04" />
        </form>
    <?php } else if (!empty($traits) and $redirect === "TRUE") {
        $t = 0;
        while ($t <= $traits['trait_count']) {
            if ($t == 0 and $traits['background_color'] === true) {
                $v = 1;
                $traits["image_layers"][$t]['rgba'] = array();
                $traits["image_layers"][$t]['weights'] = array();
                while ($v <= $traits['image_layers'][$t]['variations']) {
                    $trait_var = $t . "_" . $v;
                    $traits["image_layers"][$t]['rgba'][$_POST["trait${trait_var}_name"]] = array((int)$_POST["trait${trait_var}_r"], (int)$_POST["trait${trait_var}_g"], (int)$_POST["trait${trait_var}_b"], (int)$_POST["trait${trait_var}_a"]);
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_weight"]);
                    $v = $v + 1;
                }
            } else {
                $v = 1;
                $traits["image_layers"][$t]['filenames'] = array();
                $traits["image_layers"][$t]['weights'] = array();
                while ($v <= $traits['image_layers'][$t]['variations']) {
                    $trait_var = $t . "_" . $v;
                    $traits["image_layers"][$t]['filenames'][$_POST["trait${trait_var}_name"]] = $_POST["trait${trait_var}_file"];
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_weight"]);
                    $v = $v + 1;
                }
            }
            $t = $t + 1;
        }
        $traits_json = json_encode($traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./images/${collection_lower}/traits.json", $traits_json);
        Redirect('/4', false);
    } else {
        Redirect('/1', false);
    }
?>