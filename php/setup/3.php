<?php

    $collection_lower = $_GET['collection'];
    $traits_file = file_get_contents("./collections/${collection_lower}/config/traits.json");
    $traits = json_decode($traits_file, true);
    $s = 1;
    $t_display = $traits['trait_count'];

    if (!empty($traits) and $redirect !== "TRUE") { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <section>
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
            </section>
        </div>
        <script>
            const rarityCheck = (form) => {
                let valid = true;
                let rarities = [];
                // Build rarities array (rarities[t][v] = r => Trair 't', variation 'v' has rarity 'r'%)
                for (const input of form) {
                    const match = input.id.match(/trait(\d+)_(\d+)_rarity/);
                    if (match) {
                        const [/*ignore*/, trait, variation] = match;
                        if (rarities[trait] === undefined) {
                            rarities[trait] = [];
                        }
                        rarities[trait][variation-1] = parseInt(input.value);
                    }
                }
                // Iterate through rarities backwards and make sure the sum is 100, or display message
                const first_t = (rarities[0] === undefined) ? 1 : 0;
                for (let t = rarities.length - 1; t >= first_t; t--) {
                    console.log(t);
                    const errorH3 = document.getElementById(`trait${t}_error`);
                    const sum = rarities[t].reduce((cum, el) => cum + el, 0);
                    if (sum !== 100) {
                        errorH3.innerHTML = `The rarity percentages should add up to 100% (not ${sum}%)`;
                        errorH3.hidden = false;
                        window.location.hash = `trait${t}`;
                        valid = false;
                    }
                    else {
                        errorH3.innerHTML = 'No error'
                        errorH3.hidden = true;
                    }
                }
                return valid;
            }
        </script>
        <form enctype="multipart/form-data" onSubmit="return rarityCheck(this);" method="post" action="/setup/3?collection=<?php echo $collection_lower; ?>">
            <?php $t = 0;
            while ($s <= $traits['trait_count']) {
                if ($t == 0 and $traits['background_color'] === true) { ?>
                    <h3 class="trait-title" id="trait<?php echo $s; ?>">Setup Background Colors:</h3>
                    <h3 hidden class="error" id="trait<?php echo $s; ?>_error">No error</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $s . "_" . $v; ?>
                        <h4>Color #<?php echo $v ?>:</h4>
                        <div data-tooltip="Color Display Name: The pretty name of this variation (show in the metadata)"><input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Color Display Name" /></div>
                        <div class="trait-row">
                            <div data-tooltip="Rarity: Chance for this variation to be picked, in percent (all values within a trait should add up to 100)">
                                <label for="trait<?php echo $trait_var ?>_rarity">Set Rarity:</label><br />
                                <input required type="number" class="form small" id="trait<?php echo $trait_var ?>_rarity" min="0" max="100" name="trait<?php echo $trait_var ?>_rarity" placeholder="0-100">&nbsp;%
                            </div>
                            <div data-tooltip="Color: The color of this background variation">
                                <label for="trait<?php echo $trait_var ?>_r">Color:</label><br />
                                <input required type="color" class="form small" id="trait<?php echo $trait_var ?>_color" name="trait<?php echo $trait_var ?>_color" />
                            </div>
                            <div data-tooltip="Opacity: The transparency of this background variation&#xa;(0: invisible, 255: opaque)">
                                <label for="trait<?php echo $trait_var ?>_a">Opacity:</label><br />
                                <input required type="number" class="form small" id="trait<?php echo $trait_var ?>_alpha" min="0" max="255" name="trait<?php echo $trait_var ?>_alpha" placeholder="0-255" value="255"/>
                            </div>
                        </div>
                    <?php $v = $v + 1; }
                } else { ?>
                    <h3 class="trait-title" id="trait<?php echo $s; ?>">Setup "<?php echo $traits['image_layers'][$t]['layer_name'] ?>" Trait:</h3>
                    <h3 hidden class="error" id="trait<?php echo $s; ?>_error">No error</h3>
                    <?php $v = 1; while ($v <= $traits['image_layers'][$t]['variations']) {
                        $trait_var = $s . "_" . $v; ?>
                        <h4>Variation #<?php echo $v ?>:</h4>
                        <div data-tooltip="Variation Name: The pretty name of this variation (shown in the metadata)"><input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Variation #<?php echo $v ?> Name" /></div>
                        <div class="trait-row">
                            <div data-tooltip="Rarity: Chance for this variation to be picked, in percent (all values within a trait should add up to 100)">
                                <label for="trait<?php echo $trait_var ?>_rarity">Set Rarity:</label><br />
                                <input required type="number" class="form small" id="trait<?php echo $trait_var ?>_rarity" min="0" max="100" name="trait<?php echo $trait_var ?>_rarity" placeholder="0-100">&nbsp;%
                            </div>
                            <div data-tooltip="Image File: Pick the image file for this variation.&#xa;(Browse or drag'n'drop)">
                                <label for="trait<?php echo $trait_var ?>_r">Image File:</label><br />
                                <input required type="file" class="form med" id="trait<?php echo $trait_var ?>_file" name="trait<?php echo $trait_var ?>_file" />
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
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_rarity"]);
                    $v = $v + 1;
                }
            } else {
                $v = 1;
                $traits["image_layers"][$t]['filenames'] = array();
                $traits["image_layers"][$t]['weights'] = array();
                while ($v <= $traits['image_layers'][$t]['variations']) {
                    $trait_var = $s . "_" . $v;
                    $traits["image_layers"][$t]['filenames'][$_POST["trait${trait_var}_name"]] = $_FILES["trait${trait_var}_file"]['name'];
                    array_push($traits["image_layers"][$t]['weights'], (int)$_POST["trait${trait_var}_rarity"]);
                    $target_file = $target_dir . "/" . $_FILES["trait${trait_var}_file"]['name'];
                    move_uploaded_file($_FILES["trait${trait_var}_file"]['tmp_name'], $target_file);
                    $v = $v + 1;
                }
            }
            $t = $t + 1;
            $s = $s + 1;
        }
        $traits_json = json_encode($traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./collections/${collection_lower}/config/traits.json", $traits_json);
        Redirect("/setup/finish?collection=${collection_lower}", false);
    } else {
        Redirect('/setup/1', false);
    }

?>