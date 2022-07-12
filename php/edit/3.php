<?php

    $collection = $_GET['collection'];
    $traits_file = file_get_contents("./collections/${collection}/config/traits.json");
    $new_traits_file = file_get_contents("./collections/${collection}/config/traits.tmp.json");
    $traits = json_decode($traits_file, true);
    $new_traits = json_decode($new_traits_file, true);
    $s = 1;
    $t_display = $new_traits['trait_count'];

    if (!empty($new_traits) and $redirect !== "TRUE") { ?>
        <h3>Collection Info</h3>
        <div id="guide">
            <section>
                <p>STEP 03 - Define filenames, colors and rarities for each variation.</p>
                <p><b>Collection Name</b>: <?php echo $new_traits['collection_name'] ?></p>
                <?php if (array_key_exists('artist_name', $new_traits)) {
                    echo "<p><b>Artist's Name</b>: " . $new_traits['artist_name'] . "</p>";
                } ?>
                <?php if (array_key_exists('royalty_address', $new_traits)) {
                    echo "<p><b>Royalty Address</b>: " . $new_traits['royalty_address'] . "</p>";
                } ?>
                <?php if ($new_traits['background_color'] === true) {
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
                    const match = input.id.match(/trait(\d+)_(\d+|empty)_rarity/);
                    if (match) {
                        const [/*ignore*/, trait, variation] = match;
                        if (rarities[trait] === undefined) {
                            rarities[trait] = [];
                        }
                        if (variation === 'empty') {
                            rarities[trait]['empty'] = parseFloat(input.value);
                        } else {
                            rarities[trait][variation-1] = parseFloat(input.value);
                        }
                    }
                }
                // Iterate through rarities backwards and make sure the sum is 100, or display message
                const first_t = (rarities[0] === undefined) ? 1 : 0;
                for (let t = rarities.length - 1; t >= first_t; t--) {
                    const errorH3 = document.getElementById(`trait${t}_error`);
                    const sum = rarities[t].reduce((cum, el) => cum + el, 0) + rarities[t]['empty'];
                    if (abs(sum - 100) > 1e-6) {    // Float comparison for sum == 100, avoids rounding errors
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
            const setNameFromFilename = (fileInput) => {
                const nameInput = document.getElementById(fileInput.id.replace("_file", "_name"));
                if (fileInput === null || fileInput.files === null || fileInput.files.length === 0 ||
                    nameInput === null || nameInput.value.length > 0) {
                return;
                }
                const fileName = fileInput.files[0].name;
                let name = fileName.replace(/\.[^/.]+$/, ""); // Strip the extension
                name = name.replace(/[_-]/g, " "); // Replace underscores and hyphens with spaces
                name = name.replace(/(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])/g, " "); // Add space between number and letter
                name = name.replace(/\s+/g, " ").trim(); // Remove multiple spaces and trim whitespaces
                name = name.split(" ")
                        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(" "); // Capitalize first letter of each word
                nameInput.value = name;
            };
        </script>
        <form enctype="multipart/form-data" onSubmit="return rarityCheck(this);" method="post" action="/edit/3?collection=<?php echo $collection; ?>">
            <?php $t = 0;
            while ($s <= $new_traits['trait_count']) {
                if ($t == 0 and $new_traits['background_color'] === true) { // Background color layer
                    unset($layer);
                    $weights_empty = false;
                    if (($traits['background_color'] === true) and isset($traits['image_layers'][$s])) {
                        $layer = $traits["image_layers"][$s];
                        if (isset($layer['weights_total']) && isset($layer['weights'])) {
                            $weights_empty = $layer['weights_total'] - array_sum($layer['weights']);
                        }
                    } ?>
                    <h3 class="trait-title" id="trait<?php echo $s; ?>">Setup Background Colors:</h3>
                    <h3 hidden class="error" id="trait<?php echo $s; ?>_error">No error</h3>
                    <?php $v = 1; while ($v <= $new_traits["image_layers"][$s]['variations']) { // Background color variations
                        $trait_var = $s . "_" . $v;
                        unset($var_name);
                        if (isset($layer) and isset($layer['weights'][$v - 1])) {
                            $var_name = array_keys($layer['rgba'])[$v - 1];
                            $rgb = array_slice($layer['rgba'][$var_name], 0, 3);
                            $color_hex = '#' . implode('', array_map(function ($element) {
                                return sprintf('%02X', $element);
                            }, $rgb));
                            $opacity = $layer['rgba'][$var_name][3];
                        } ?>
                        <hr class="hrtop" />
                        <div>
                            <h4>Color #<?php echo $v ?>:</h4>
                            <div data-tooltip="Display Name: The pretty name of this variation">
                                <input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Color Display Name" value="<?php echo isset($var_name) ? $var_name : null; ?>" />
                            </div>
                            <div class="trait-row">
                                <div data-tooltip="Color: The color of this background variation">
                                    <label for="trait<?php echo $trait_var ?>_r">Color:</label><br />
                                    <input required type="color" class="form small" id="trait<?php echo $trait_var ?>_color" name="trait<?php echo $trait_var ?>_color" value="<?php echo isset($var_name) ? $color_hex : '#000000'; ?>" />
                                </div>
                                <div data-tooltip="Opacity: The transparency of this background variation&#xa;(0: invisible, 255: opaque)">
                                    <label for="trait<?php echo $trait_var ?>_a">Opacity:</label><br />
                                    <input required type="number" class="form small" id="trait<?php echo $trait_var ?>_alpha" min="0" max="255" name="trait<?php echo $trait_var ?>_alpha" placeholder="0-255" value="<?php echo isset($var_name) ? $opacity : 255; ?>" />
                                </div>
                                <div data-tooltip="Rarity: Chance for this variation to be picked, in percent">
                                    <label for="trait<?php echo $trait_var ?>_rarity">Set Rarity:</label><br />
                                    <input required type="number" step="any" class="form small" id="trait<?php echo $trait_var ?>_rarity" min="0" max="100" name="trait<?php echo $trait_var ?>_rarity" placeholder="0-100"  value="<?php echo isset($var_name) ? $layer['weights'][$v-1] : null; ?>">&nbsp;%
                                </div>
                            </div>
                        </div>
                        <hr class="hrbottom" />
                    <?php $v = $v + 1; }
                } else { // Image layers
                    $s_offset = 0;
                    if ($traits['background_color'] === false) { $s_offset = -1; }
                    unset($layer);
                    $weights_empty = false;
                    if (isset($traits['image_layers'][$s + $s_offset])) {
                        $layer = $traits["image_layers"][$s + $s_offset];
                        if (isset($layer['weights_total']) && isset($layer['weights'])) {
                            $weights_empty = $layer['weights_total'] - array_sum($layer['weights']);
                        }
                    } ?>
                    <h3 class="trait-title" id="trait<?php echo $s; ?>">Setup "<?php echo $new_traits['image_layers'][$t]['layer_name']; ?>" Trait:</h3>
                    <h3 hidden class="error" id="trait<?php echo $s; ?>_error">No error</h3>
                    <?php $v = 1; while ($v <= $new_traits['image_layers'][$t]['variations']) { // Image layers variations
                        $trait_var = $s . "_" . $v;
                        unset($var_name);
                        if (isset($layer) and isset($layer['weights'][$v - 1])) {
                            $var_name = array_keys($layer['filenames'])[$v - 1];
                            $filename = $layer['filenames'][$var_name];
                            $filepath =  "./collections/" . $collection . "/config/source_layers/layer" . sprintf('%02d', $s) . "/" . $filename;
                            $file_exists = file_exists($filepath);
                        } ?>
                        <hr class="hrtop" />
                        <h4>Variation #<?php echo $v ?>:</h4>
                        <div data-tooltip="Display Name: The pretty name of this variation">
                            <input required type="text" class="form wide" id="trait<?php echo $trait_var ?>_name" name="trait<?php echo $trait_var ?>_name" placeholder="Variation #<?php echo $v ?> Name" value="<?php echo isset($var_name) ? $var_name : null; ?>" />
                        </div>
                        <div class="trait-row">
                            <div data-tooltip="Image: Pick the image file for this variation.&#xa;(Browse or drag'n'drop)">
                                <label for="trait<?php echo $trait_var ?>_r">Filename:</label><br />
                                <?php if (isset($var_name) and $file_exists) {  // File exists, pre-fill field with filename (no need to upload it again) ?>
                                    <input required type="text" class="form med" id="trait<?php echo $trait_var ?>_file" name="trait<?php echo $trait_var ?>_file" value="<?php echo isset($var_name) ? $filename : null; ?>" onclick="this.type='file'" oninput="this.type='file'" />
                                <?php } else {  // File does not exist, create a file input field (need to upload the file on submission) ?>
                                    <input required type="file" class="form med" id="trait<?php echo $trait_var ?>_file" name="trait<?php echo $trait_var ?>_file" onChange="setNameFromFilename(this);" />
                                <?php } ?>
                            </div>
                            <div data-tooltip="Rarity: Chance for this variation to be picked, in percent">
                                <label for="trait<?php echo $trait_var ?>_rarity">Set Rarity:</label><br />
                                <input required type="number" step="any" class="form small" id="trait<?php echo $trait_var ?>_rarity" min="0" max="100" name="trait<?php echo $trait_var ?>_rarity" placeholder="0-100"  value="<?php echo isset($var_name) ? $layer['weights'][$v-1] : null; ?>">&nbsp;%
                            </div>
                        </div>
                        <hr class="hrbottom" />
                    <?php $v = $v + 1; }
                }
                $trait_var = $s . "_empty"; ?>
                <div class="trait-row" data-tooltip="Chance for the whole layer to be skipped, in percent">
                    <h5 class="small">Skip layer:</h5>
                    <div>
                        <label for="trait<?php echo $trait_var ?>_rarity">Set Rarity:</label>
                        <input required type="number" step="any" class="form small" id="trait<?php echo $trait_var ?>_rarity" min="0" max="100" name="trait<?php echo $trait_var ?>_rarity" placeholder="0-100" value="<?php echo $weights_empty === false ? null : $weights_empty; ?>">&nbsp;%
                    </div>
                </div>
                <?php
                $t = $t + 1;
                $s = $s + 1;
            } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="FINISH" />
        </form>
    <?php } else if (!empty($new_traits) and $redirect === "TRUE") {
        $t = 0;
        if ($new_traits['background_color'] === true) { $s = 0; } else { $s = 1; }
        while ($s <= $new_traits['trait_count']) {
            $target_dir = "./collections/" . $collection . "/config/source_layers/layer" . sprintf('%02d', $s);
            if (!file_exists($target_dir)) {
                mkdir($target_dir, 0755, true);
            }
            if ($t == 0 and $new_traits['background_color'] === true) {
                $v = 1;
                $new_traits["image_layers"][$t]['rgba'] = array();
                $new_traits["image_layers"][$t]['weights'] = array();
                while ($v <= $new_traits['image_layers'][$t]['variations']) {
                    $trait_var = $s . "_" . $v;
                    $rgb = str_split(str_replace("#", "", $_POST["trait${trait_var}_color"]), 2);
                    $new_traits["image_layers"][$t]['rgba'][$_POST["trait${trait_var}_name"]] = array(hexdec($rgb[0]), hexdec($rgb[1]), hexdec($rgb[2]), (int)$_POST["trait${trait_var}_alpha"]);
                    array_push($new_traits["image_layers"][$t]['weights'], (float)$_POST["trait${trait_var}_rarity"]);
                    $v = $v + 1;
                }
                $new_traits["image_layers"][$t]['weights_total'] = (float)$_POST["trait${s}_empty_rarity"] + array_sum($new_traits["image_layers"][$t]['weights']); // Should be 100
            } else {
                $v = 1;
                $new_traits["image_layers"][$t]['filenames'] = array();
                $new_traits["image_layers"][$t]['weights'] = array();
                while ($v <= $new_traits['image_layers'][$t]['variations']) {
                    $trait_var = $s . "_" . $v;
                    $var_name = $_POST["trait${trait_var}_name"];
                    $var_weight = (float)$_POST["trait${trait_var}_rarity"];

                    if (isset($_FILES["trait${trait_var}_file"])) { // New file was uploaded
                        $filename = $_FILES["trait${trait_var}_file"]['name'];
                        // Move newly uploaded file to correct directory
                        $target_file = $target_dir . "/" . $filename;
                        move_uploaded_file($_FILES["trait${trait_var}_file"]['tmp_name'], $target_file);
                    }
                    else if (isset($_POST["trait${trait_var}_file"])) { // Old file should be re-used
                        $filename = $_POST["trait${trait_var}_file"];
                        // No need to move old file
                    }
                    $new_traits["image_layers"][$t]['filenames'][$var_name] = $filename;    // Add variation filename to filename array (with variation name as key)
                    array_push($new_traits["image_layers"][$t]['weights'], $var_weight);    // Add weights to weight array
                    $v = $v + 1;
                }
                $new_traits["image_layers"][$t]['weights_total'] = (float)$_POST["trait${s}_empty_rarity"] + array_sum($new_traits["image_layers"][$t]['weights']); // Should be 100
            }
            $t = $t + 1;
            $s = $s + 1;
        }
        $new_traits_json = json_encode($new_traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./collections/${collection}/config/traits.tmp.json", $new_traits_json);
        Redirect("/edit/finish?collection=${collection}", false);
    } else {
        Redirect('/edit/1', false);
    }

?>