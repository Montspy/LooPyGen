<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Setup Info</h3>
        <div id="guide">
            <div class="section">
                <p>Fill in the following information to start setting up your collection.</p>
            </div>
        </div>
        <form method="post" action="/setup/1">
            <h3>Artist Info</h3>
            <div id="artist" class="section">
                <input required type="text" class="form wide" id="artist_name" name="artist_name" placeholder="Artist Name (Shown in metadata)" />
                <input type="text" class="form wide" id="artist_address" name="artist_address" placeholder="Artist's Address (Optional, shown in metadata)" />
            </div>
            <h3>Collection Info</h3>
            <div id="collection" class="section">
                <input required type="text" class="form wide" id="collection_name" name="collection_name" placeholder="Collection Name" />
                <input required type="text" class="form wide" id="description" name="description" placeholder="Collection Description" />
                <input type="text" class="form wide" id="seed" name="seed" placeholder="Generation Seed (Optional)" />
                <div class="row">
                    <label for="trait_count">
                        Royalty Percentage:
                    </label>
                    <input required type="number" class="form number" id="royalty_percentage" min="0" max="10" name="royalty_percentage" placeholder="0-10" />
                    <label for="trait_count">
                        How many Traits?
                    </label>
                    <input required type="number" class="form number" id="trait_count" min="2" name="trait_count" placeholder="2+" />
                    <label for="background_color">
                        Pick background colors?
                    </label>
                    <input type="checkbox" id="background_color" name="background_color" />
                </div>
            </div>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 02" />
        </form>
    <?php } else {
        $collection_name = $_POST['collection_name'];
        $description = $_POST['description'];
        $artist_name = $_POST['artist_name'];
        $trait_count = $_POST['trait_count'];
        $royalty_percentage = $_POST['royalty_percentage'];
        if (!empty($_POST['artist_address'])) { $artist_address = $_POST['artist_address']; } else { $artist_address = false; }
        if (!empty($_POST['background_color'])) { $background_color = true; } else { $background_color = false; }
        if (!empty($_POST['seed'])) { $seed = $_POST['seed']; } else { $seed = false; }
        $collection_lower = str_replace(' ', '_', strtolower($collection_name));
        $traits_file = "./images/${collection_lower}/traits.json";

        if (!file_exists("./images/${collection_lower}")) {
            mkdir("./images/${collection_lower}", 0755, true);
        }

        $traits_data = array("collection_name"=>$collection_name,
                             "description"=>$description,
                             "artist_name"=>$artist_name,
                             "royalty_percentage"=>(int)$royalty_percentage,
                             "trait_count"=>(int)$trait_count,
                             "background_color"=>$background_color);

        if ($artist_address != false) {
            $traits_data['artist_address'] = $artist_address;
        }

        if ($seed != false) {
            $traits_data['seed'] = $seed;
        }

        $traits_json = json_encode($traits_data, JSON_UNESCAPED_SLASHES|JSON_PRETTY_PRINT);
        file_put_contents($traits_file, $traits_json);
        file_put_contents(".tempfile", $collection_lower);

        Redirect('/setup/2', false);
    }
?>