<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Setup Info</h3>
        <div id="guide">
            <div class="section">
                <p>STEP 01 - Fill in the following artist and collection information.</p>
            </div>
        </div>
        <form method="post" action="/setup/1">
            <h3>Artist Info</h3>
            <div id="artist" class="section">
                <div data-tooltip="Artist Name: The name of the artist to show in the metadata [optional]"><input type="text" class="form wide" id="artist_name" name="artist_name" placeholder="Artist Name (Optional, shown in metadata)" /></div>
                <div data-tooltip="Royalty Address: The address which will receive the royalties (L2, ENS or acccount ID) [optional]"><input type="text" class="form wide" id="royalty_address" name="royalty_address" placeholder="Royalty Address (Optional)" /></div>
            </div>
            <h3>Collection Info</h3>
            <div id="collection" class="section">
                <div data-tooltip="Collection Name: A pretty name for your collection"><input required type="text" class="form wide" id="collection_name" name="collection_name" placeholder="Collection Name" /></div>
                <div data-tooltip="Collection Description: A pretty description for your collection"><input required type="text" class="form wide" id="description" name="description" placeholder="Collection Description" /></div>
                <div data-tooltip="Generation Seed: A seed for the random generator (use one for reproducible results) [optional]"><input type="text" class="form wide" id="seed" name="seed" placeholder="Generation Seed (Optional)" /></div>
                <div class="row">
                    <div data-tooltip="Royalty Percentage: Percentage of the price of a sale that will go to the Royalty Address">
                        <label for="trait_count">
                            Royalty Percentage:
                        </label>
                        <input required type="number" class="form number" id="royalty_percentage" min="0" max="10" name="royalty_percentage" placeholder="0-10" />
                    </div>
                    <div data-tooltip="Traits Count: How many traits will your NFT have (excluding background color)">
                        <label for="trait_count">
                            How many Traits?
                        </label>
                        <input required type="number" class="form number" id="trait_count" min="2" name="trait_count" placeholder="2+" />
                    </div>
                    <div data-tooltip="Background Color: Check this box to specify a set of background fill colors">
                        <label for="background_color">
                            Pick background colors?
                        </label>
                        <input type="checkbox" id="background_color" name="background_color" />
                    </div>
                </div>
            </div>
            <input type="hidden" name="redirect" id="redirect" value="TRUE" />
            <input class="form btn" type="submit" name="submit" value="STEP 02" />
        </form>
    <?php } else {
        $collection_name = $_POST['collection_name'];
        $description = $_POST['description'];
        $trait_count = $_POST['trait_count'];
        $royalty_percentage = $_POST['royalty_percentage'];
        if (!empty($_POST['artist_name'])) { $artist_name = $_POST['artist_name']; } else { $artist_name = false; }
        if (!empty($_POST['royalty_address'])) { $royalty_address = $_POST['royalty_address']; } else { $royalty_address = false; }
        if (!empty($_POST['background_color'])) { $background_color = true; } else { $background_color = false; }
        if (!empty($_POST['seed'])) { $seed = $_POST['seed']; } else { $seed = false; }
        $collection_lower = str_replace(' ', '_', strtolower($collection_name));
        $traits_file = "./images/${collection_lower}/traits.json";

        if (!file_exists("./images/${collection_lower}")) {
            mkdir("./images/${collection_lower}", 0755, true);
        }

        $traits_data = array("collection_name"=>$collection_name,
                             "collection_lower"=>$collection_lower,
                             "description"=>$description,
                             "artist_name"=>$artist_name,
                             "royalty_percentage"=>(int)$royalty_percentage,
                             "trait_count"=>(int)$trait_count,
                             "background_color"=>$background_color);

        if ($artist_name != false) {
            $traits_data['artist_name'] = $artist_name;
        }

        if ($royalty_address != false) {
            $traits_data['royalty_address'] = $royalty_address;
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