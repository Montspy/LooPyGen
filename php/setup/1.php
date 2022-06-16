<?php
    if ($redirect !== "TRUE") { ?>
        <h3>Setup Info</h3>
        <div id="guide">
            <section>
                <p>STEP 01 - Fill in the following artist and collection information.</p>
            </section>
        </div>
        <form method="post" action="/setup/1">
            <h3>Artist Info</h3>
            <section id="artist">
                <div data-tooltip="Artist Name: The name of the artist (shown in the metadata)&#xa;[optional]"><input type="text" class="form wide" id="artist_name" name="artist_name" placeholder="Artist Name (Optional, shown in metadata)" /></div>
                <div data-tooltip="Royalty Address: The address which will receive the trade royalties (L2, ENS or acccount ID)&#xa;[optional]"><input type="text" class="form wide" id="royalty_address" name="royalty_address" placeholder="Royalty Address (Optional)" /></div>
            </section>
            <h3>Collection Info</h3>
            <section id="collection">
                <div data-tooltip="Collection Name: The pretty name of the collection"><input required type="text" class="form wide" id="collection_name" name="collection_name" placeholder="Collection Name" /></div>
                <div data-tooltip="Collection Description: The pretty description of the collection"><input required type="text" class="form wide" id="description" name="description" placeholder="Collection Description" /></div>
                <div data-tooltip="Generation Seed: A seed for the random number generator (use one for reproducible results)&#xa;[optional]"><input type="text" class="form wide" id="seed" name="seed" placeholder="Generation Seed (Optional)" /></div>
                <div class="row">
                    <div data-tooltip="Royalty Percentage: How much of the sell price will go to the Royalty Address during a trade">
                        <label for="trait_count">
                            Royalty Percentage:
                        </label>
                        <input required type="number" class="form number" id="royalty_percentage" min="0" max="10" name="royalty_percentage" placeholder="0-10" />&nbsp;%
                    </div>
                    <div data-tooltip="Traits Count: How many traits/layers your NFT has">
                        <label for="trait_count">
                            How many Traits?
                        </label>
                        <input required type="number" class="form number" id="trait_count" min="2" name="trait_count" placeholder="2+" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Background Color: Check this box for LooPyGen to add background colors behind your NFT">
                        <label for="background_color">
                            Add background colors?
                        </label>
                        <input type="checkbox" id="background_color" name="background_color" />
                    </div>
                    <div data-tooltip="Thumbnails: Check this box for LooPyGen to generate thumbnails of your NFTs for faster previews and widest compatibility with wallets">
                        <label for="thumbnails">
                            Generate thumbnails?
                        </label>
                        <input type="checkbox" id="thumbnails" name="thumbnails" />
                    </div>
                    <div data-tooltip="Animated collection: Check this box to indicate that this collection contains animated traits (GIF, MP4 or WebM)">
                        <label for="animation">
                            Animated collection?
                        </label>
                        <input type="checkbox" id="animation" name="animation" />
                    </div>
                </div>
            </section>
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
        if (!empty($_POST['thumbnails'])) { $thumbnails = true; } else { $thumbnails = false; }
        if (!empty($_POST['animation'])) { $animation = true; } else { $animation = false; }
        if (!empty($_POST['seed'])) { $seed = $_POST['seed']; } else { $seed = false; }
        $collection_lower = sanitize($collection_name);
        $traits_file = "./collections/${collection_lower}/config/traits.json";

        if (!file_exists("./collections/${collection_lower}/config")) {
            mkdir("./collections/${collection_lower}/config/source_layers", 0755, true);
            mkdir("./collections/${collection_lower}/ipfs", 0755, true);
            mkdir("./collections/${collection_lower}/stats", 0755, true);
        }

        $traits_data = array("collection_name"=>$collection_name,
                             "collection_lower"=>$collection_lower,
                             "description"=>$description,
                             "artist_name"=>$artist_name,
                             "thumbnails"=>$thumbnails,
                             "animation"=>$animation,
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

        Redirect("/setup/2?collection=${collection_lower}", false);
    }

?>