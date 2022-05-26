<?php

    $collection_lower = file_get_contents(".tempfile");
    $traits_file = file_get_contents("./collections/${collection_lower}/config/traits.json");
    $traits = json_decode($traits_file, true);
    $s = 1;
    $t_display = $traits['trait_count'];

    if (!empty($traits) and $redirect !== "TRUE") { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <div class="section">
                <p>STEP 03 - Define filenames, colors and rarities for each variation.</p>
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
        <form method="post" action="/setup/3">
            <?php $t = 0;
            while ($s <= $traits['trait_count']) {
                if ($t == 0 and $traits['background_color'] === true) { ?>
                    <h3 class="trait-title">Setup Background Colors:</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $s . "_" . $v; ?>
                        <h4>Color #<?php echo $v ?>:</h4>
                        <div data-tooltip="Display Name: The pretty name of this variation"><input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Color Display Name" /></div>
                        <div class="trait-row wide">
                            <div class="trait-row" data-tooltip="Rarity: How rare this variation is">
                                <label for="trait<?php echo $trait_var ?>_weight">Set Rarity:&nbsp;&nbsp;</label>
                                <select required class="form" id="trait<?php echo $trait_var ?>_weight" name="trait<?php echo $trait_var ?>_weight">
                                    <option value="4">Common</option>
                                    <option value="3">Uncommon</option>
                                    <option value="2">Rare</option>
                                    <option value="1">Legendary</option>
                                </select>
                            </div>
                            <div class="trait-row" data-tooltip="Color: The fill color of this background variation">
                                <label for="trait<?php echo $trait_var ?>_r">Color:&nbsp;&nbsp;</label>
                                <input required type="color" class="form small" id="trait<?php echo $trait_var ?>_color" name="trait<?php echo $trait_var ?>_color" />
                            </div>
                            <div class="trait-row small" data-tooltip="Opacity: The transparency of this background variation (0: invisible, 255: opaque)">
                                <label for="trait<?php echo $trait_var ?>_a">Opacity:&nbsp;&nbsp;</label>
                                <input required type="number" class="form number" id="trait<?php echo $trait_var ?>_alpha" min="0" max="255" name="trait<?php echo $trait_var ?>_alpha" placeholder="0-255" />
                            </div>
                        </div>
                    <?php $v = $v + 1; }
                } else { ?>
                    <h3 class="trait-title">Setup "<?php echo $traits['image_layers'][$t]['layer_name'] ?>" Trait:</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $s . "_" . $v; ?>
                        <h4>Variation #<?php echo $v ?>:</h4>
                        <div data-tooltip="Display Name: The pretty name of this variation"><input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Variation #<?php echo $v ?> Name" /></div>
                        <div class="trait-row wide">
                            <div data-tooltip="Rarity: How rare this variation is">
                                <label for="trait<?php echo $trait_var ?>_weight">Set Rarity:&nbsp;&nbsp;</label>
                                <select required class="form" id="trait<?php echo $trait_var ?>_weight" name="trait<?php echo $trait_var ?>_weight">
                                    <option value="4">Common</option>
                                    <option value="3">Uncommon</option>
                                    <option value="2">Rare</option>
                                    <option value="1">Legendary</option>
                                </select>
                            </div>
                            <div data-tooltip="Filename: The exact name of the trait/layer file">
                                <label for="trait<?php echo $trait_var ?>_r">Filename:&nbsp;&nbsp;</label>
                                <input required type="file" class="form" id="trait<?php echo $trait_var ?>_file" name="trait<?php echo $trait_var ?>_file" />
                            </div>
                        </div>
                    <?php $v = $v + 1; }
                }
                $t = $t + 1;
                $s = $s + 1;
            } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="FINISH" />
        </form>
    <?php } else if (!empty($traits) and $redirect === "TRUE") {
        $t = 0;
        if ($traits['background_color'] === true) { $s = 0; } else { $s = 1; }
        while ($s <= $traits['trait_count']) {
            $target_dir = "./collections/" . $traits['collection_lower'] . "/config/source_layers/layer" . sprintf('%02d', $s);;
            if (!file_exists($target_dir)) {
                mkdir($target_dir, 0755, true);
            }
            if ($t == 0 and $traits['background_color'] === true) {
                $v = 1;
                $traits["image_layers"][$t]['rgba'] = array();
                $traits["image_layers"][$t]['weights'] = array();
                while ($v <= $traits['image_layers'][$t]['variations']) {
                    $trait_var = $s . "_" . $v;
                    $rgb = str_split(str_replace("#", "", $_POST["trait${trait_var}_color"]), 2);
                    $traits["image_layers"][$t]['rgba'][$_POST["trait${trait_var}_name"]] = array(hexdec($rgb[0]), hexdec($rgb[1]), hexdec($rgb[2]), (int)$_POST["trait${trait_var}_alpha"]);
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_weight"]);
                    $v = $v + 1;
                }
            } else {
                $v = 1;
                $traits["image_layers"][$t]['filenames'] = array();
                $traits["image_layers"][$t]['weights'] = array();
                while ($v <= $traits['image_layers'][$t]['variations']) {
                    $trait_var = $s . "_" . $v;
                    $traits["image_layers"][$t]['filenames'][$_POST["trait${trait_var}_name"]] = $_POST["trait${trait_var}_file"];
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_weight"]);
                    $target_file = $target_dir . $_FILES["trait${trait_var}_file"]['name'];
                    move_uploaded_file($_FILES["trait${trait_var}_file"]['temp_name'], $target_file))
                    $v = $v + 1;
                }
            }
            $t = $t + 1;
            $s = $s + 1;
        }
        $traits_json = json_encode($traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./collections/${collection_lower}/config/traits.json", $traits_json);
        Redirect('/setup/finish', false);
    } else {
        Redirect('/setup/1', false);
    }

?>