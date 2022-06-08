<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    if (empty($_GET['collection'])) {
        echo '<h1>Edit Traits</h1>';
        echo '<h3>Choose a collection:</h3>';
        echo '<div class="nav">';
        $found = 0;
        foreach ($collections as $c) {
            if ($c !== ".keep") {
                $cf = "./collections/${c}/config/traits.json";
                if (file_exists($cf)) {
                    $ctf = file_get_contents($cf);
                    $ct = json_decode($ctf, true);
                    $lower = $ct['collection_lower'];
                    $name = $ct['collection_name'];
                    echo "<a href=\"/edit/1?collection=${lower}\">${name}</a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1">CREATE NEW COLLECTION</a>';
        }
        echo '</div>';
    } else if ($redirect !== "TRUE") {
        if (!empty($_GET['collection'])) {
            $lower = $_GET['collection'];
            $file = "./collections/${lower}/config/traits.json";
            $contents = file_get_contents($file);
            $traits = json_decode($contents, true);

            $collection_name = $traits['collection_name'];
            $collection_lower = $traits['collection_lower'];
            $description = $traits['description'];
            $artist_name = $traits['artist_name'] ?? '';
            $thumbnails = $traits['thumbnails'];
            $animation = $traits['animation'];
            $royalty_percentage = $traits['royalty_percentage'];
            $royalty_address = $traits['royalty_address'] ?? '';
            $seed = $traits['seed'] ?? '';
            $trait_count = $traits['trait_count'];
            $background_color = $traits['background_color'];
        }

        ?>
        <h1>Edit Traits</h1>
        <h3>Setup Info</h3>
        <div id="guide">
            <section>
                <p>STEP 01 - Fill in the following artist and collection information.</p>
            </section>
        </div>
        <form method="post" action="/edit/1?collection=<?php echo $lower ?>">
            <h3>Artist Info</h3>
            <section id="artist">
                <div data-tooltip="Artist Name: The name of the artist to show in the metadata [optional]"><input type="text" class="form wide" id="artist_name" name="artist_name" placeholder="Artist Name (Optional, shown in metadata)" value="<?php echo htmlspecialchars($artist_name); ?>" /></div>
                <div data-tooltip="Royalty Address: The address which will receive the royalties (L2, ENS or acccount ID) [optional]"><input type="text" class="form wide" id="royalty_address" name="royalty_address" placeholder="Royalty Address (Optional)" value="<?php echo htmlspecialchars($royalty_address); ?>" /></div>
            </section>
            <h3>Collection Info</h3>
            <section id="collection">
                <div data-tooltip="Collection Name: A pretty name for your collection"><input required type="text" class="form wide" id="collection_name" name="collection_name" placeholder="Collection Name" value="<?php echo htmlspecialchars($collection_name); ?>" /></div>
                <div data-tooltip="Collection Description: A pretty description for your collection"><input required type="text" class="form wide" id="description" name="description" placeholder="Collection Description" value="<?php echo htmlspecialchars($description); ?>" /></div>
                <div data-tooltip="Generation Seed: A seed for the random generator (use one for reproducible results) [optional]"><input type="text" class="form wide" id="seed" name="seed" placeholder="Generation Seed (Optional)" value="<?php echo htmlspecialchars($seed); ?>" /></div>
                <div class="row">
                    <div data-tooltip="Royalty Percentage: Percentage of the price of a sale that will go to the Royalty Address">
                        <label for="trait_count">
                            Royalty Percentage:
                        </label>
                        <input required type="number" class="form number" id="royalty_percentage" min="0" max="10" name="royalty_percentage" placeholder="0-10" value="<?php echo htmlspecialchars($royalty_percentage); ?>" />
                    </div>
                    <div data-tooltip="Traits Count: How many traits will your NFT have (excluding background color)">
                        <label for="trait_count">
                            How many Traits?
                        </label>
                        <input required type="number" class="form number" id="trait_count" min="2" name="trait_count" placeholder="2+" value="<?php echo htmlspecialchars($trait_count); ?>" />
                    </div>
                </div>
                <div class="row">
                    <div data-tooltip="Background Color: Check this box to specify a set of background fill colors">
                        <label for="background_color">
                            Pick background colors?
                        </label>
                        <input type="checkbox" id="background_color" name="background_color" <?php echo $background_color ? 'checked' : ''; ?> />
                    </div>
                    <div data-tooltip="Thumbnails: Check this box to include a thumbnail in your NFTs for faster previews and widest compatibility with dAPPs">
                        <label for="thumbnails">
                            Generate thumbnails?
                        </label>
                        <input type="checkbox" id="thumbnails" name="thumbnails" <?php echo $thumbnails ? 'checked' : ''; ?> />
                    </div>
                    <div data-tooltip="Animated collection: Check this box to indicate that this collection contains animated traits (GIF, MP4 or WebM)">
                        <label for="animation">
                            Animated collection?
                        </label>
                        <input type="checkbox" id="animation" name="animation" <?php echo $animation ? 'checked' : ''; ?> />
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
        $lower = $_GET['collection'];
        $traits_file = "./collections/${lower}/config/traits.tmp.json";

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

        Redirect("/edit/2?collection=${lower}", false);
    }

?>