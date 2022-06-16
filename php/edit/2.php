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
                <p>STEP 02 - Define trait names and how many variations each will have.</p>
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
        <form method="post" action="/edit/2?collection=<?php echo $collection; ?>">
            <?php if ($new_traits['thumbnails'] === true) {
                $w = (isset($traits['thumbnail_size']) and count($traits['thumbnail_size']) >= 1) ? $traits['thumbnail_size'][0] : null;
                $h = (isset($traits['thumbnail_size']) and count($traits['thumbnail_size']) >= 2) ? $traits['thumbnail_size'][1] : null;
                ?>
                <div class="trait-row" data-tooltip="Thumbnail Size: The dimensions in pixels of your thumbnails&#xa;[height: optional]">
                    <label>
                        Thumbnail size:
                    </label>
                    <div class="labeled">
                        <input required type="number" class="form size" id="thumbnail_width" min="1" name="thumbnail_width" placeholder="WIDTH" value="<?php echo $w; ?>" />x
                        <input type="number" class="form size" id="thumbnail_height" min="1" name="thumbnail_height" placeholder="HEIGHT" value="<?php echo $h; ?>" />
                    </div>
                </div>
            <?php } if ($new_traits['animation'] === true) {
                $format = isset($traits['animation']) ? $traits['animation'] : null;
                ?>
                <div class="trait-row" data-tooltip="Animated file format: The file format for animated NFTs (does not affect thumbnails).&#xa;- GIF: quickest export, largest file.&#xa;- WebM: Slower export, small file.&#xa;- MP4: Slower export, small file, no transparency">
                    <label for="animated_format">
                        Animation file format:
                    </label>
                    <select required class="form small" id="animated_format" name="animated_format" value="<?php echo $format; ?>" >
                        <option value=".gif">GIF</option>
                        <option value=".webm">WEBM</option>
                        <option value=".mp4">MP4</option>
                    </select>
                </div>
            <?php } ?>
            <h3>Setup your Traits</h3>
            <?php  $i = 0; while ($s <= $new_traits['trait_count']) {
                if ($new_traits['background_color'] === true and $i == 0) {
                    unset($layer);
                    if (($traits['background_color'] === true) and isset($traits['image_layers'][$i])) {
                        $layer = $traits["image_layers"][$i];
                        $x = (isset($layer['size']) and count($layer['size']) >= 1) ? $layer['size'][0] : null;
                        $y = (isset($layer['size']) and count($layer['size']) >= 2) ? $layer['size'][1] : null;
                    }
                    ?>
                    <h4>Setup Background Color Trait:</h4>
                    <div class="trait-row">
                        <div data-tooltip="Display Name: The pretty name of this trait/layer">
                            <input required type="text" class="form med" id="trait<?php echo $s ?>_name" name="trait<?php echo $s ?>_name" value="<?php echo isset($layer) ? $layer['layer_name'] : null; ?>" placeholder="Background Display Name" />
                        </div>
                        <div class="labeled" data-tooltip="Colors Count: The number of possible background colors">
                            <label for="trait<?php echo $s ?>_vars">
                                How many variations?
                            </label>
                            <input required type="number" class="form number" id="trait<?php echo $s ?>_vars" min="1" name="trait<?php echo $s ?>_vars" placeholder="1" value="<?php echo isset($layer) ? $layer['variations'] : null; ?>" />
                        </div>
                    </div>
                    <div class="trait-row" data-tooltip="Image Size: The dimensions in pixels of your images">
                        <label>
                            Size of your images:
                        </label>
                        <div class="labeled">
                            <input required type="number" class="form size" id="trait<?php echo $s ?>_x" min="1" name="trait<?php echo $s ?>_x" placeholder="WIDTH" value="<?php echo $x ?>" />x
                            <input required type="number" class="form size" id="trait<?php echo $s ?>_y" min="1" name="trait<?php echo $s ?>_y" placeholder="HEIGHT" value="<?php echo $y ?>" />
                        </div>
                    </div>
                <?php } else {
                    $i_offset = 0;
                    if ($traits['background_color'] === true and $new_traits['background_color'] === false) { $i_offset = 1; }
                    else if ($traits['background_color'] === false and $new_traits['background_color'] === true) { $i_offset = -1; }
                    unset($layer);
                    if (isset($traits["image_layers"][$i + $i_offset])) {
                        $layer = $traits["image_layers"][$i + $i_offset];
                    }
                    ?>
                    <h4>Setup Trait #<?php echo $s ?>:</h4>
                    <div class="trait-row">
                        <div data-tooltip="Display Name: The pretty name of this trait/layer">
                            <input required type="text" class="form med" id="trait<?php echo $s ?>_name" name="trait<?php echo $s ?>_name" placeholder="Trait #<?php echo $s ?> Display Name" value="<?php echo isset($layer) ? $layer['layer_name'] : null; ?>" />
                        </div>
                        <div class="labeled" data-tooltip="Variations Count: The number of possible values for this trait/layer">
                            <label for="trait<?php echo $s ?>_vars">
                                How many variations?
                            </label>
                            <input required type="number" class="form number" id="trait<?php echo $s ?>_vars" min="1" name="trait<?php echo $s ?>_vars" placeholder="1" value="<?php echo isset($layer) ? $layer['variations'] : null; ?>" />
                        </div>
                    </div>
            <?php } $i = $i + 1; $s = $s + 1; } ?>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 03" />
        </form>
    <?php } else if (!empty($new_traits) and $redirect === "TRUE") {
        $i = 0;
        if ($new_traits['background_color'] === true) { $s = 0; } else { $s = 1; }
        if ($new_traits['animation'] === true) {
            $new_traits['animated_format'] = $_POST['animated_format'];
        }
        $new_traits["image_layers"] = array();
        if (!empty($_POST['thumbnail_width'])) {
            if (!empty($_POST['thumbnail_height'])) {
                $thumbnail_size = array((int)$_POST['thumbnail_width'], (int)$_POST['thumbnail_height']);
            } else {
                $thumbnail_size = array((int)$_POST['thumbnail_width'], (int)$_POST['thumbnail_width']);
            }
            $new_traits['thumbnail_size'] = $thumbnail_size;
        }
        while ($s <= $new_traits['trait_count']) {
            $new_traits["image_layers"][$i]["variations"] = (int)$_POST["trait${s}_vars"];
            $new_traits["image_layers"][$i]["layer_name"] = $_POST["trait${s}_name"];
            if ($new_traits['background_color'] === true and $i == 0) {
                $new_traits["image_layers"][$i]["size"] = array((int)$_POST["trait${s}_x"], (int)$_POST["trait${s}_y"]);
            }
            $i = $i + 1;
            $s = $s + 1;
        }
        $new_traits_json = json_encode($new_traits, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents("./collections/${collection}/config/traits.tmp.json", $new_traits_json);
        Redirect("/edit/3?collection=${collection}", false);
    } else {
        Redirect('/edit/1', false);
    }

?>