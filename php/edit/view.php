<?php

    $path = "./collections";
    $collections = array_diff(scandir($path), array('.', '..'));

    echo '<h1>Edit Traits</h1>';

    if (empty($_GET['collection'])) {
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
                    echo "<a href=\"/edit/view?collection=${lower}\">${name}</a>";
                    $found = $found + 1;
                }
            }
        }
        if ($found == 0) {
            echo '<h3 class="error">No collections found.</h3>';
            echo '<a href="/setup/1">CREATE NEW COLLECTION</a>';
        }
        echo '</div>';
    } else if (empty($_GET['run'])) {
        $lower = $_GET['collection'];
        $file = "./collections/${lower}/config/traits.json";
        $contents = file_get_contents($file);
        $traits = json_decode($contents, true); ?>
        <h3>Collection Details</h3>
        <table>
            <tr>
                <td>Description:</td>
                <td><?php echo $traits['description']; ?></td>
            </tr>
            <tr>
                <td>Artist Name:</td>
                <td><?php echo $traits['artist_name']; ?></td>
            </tr>
            <?php if (isset($traits['royalty_address'])) { ?>
                <tr>
                    <td>Royalty Address:</td>
                    <td><?php echo $traits['royalty_address']; ?></td>
                </tr>
            <?php } ?>
            <tr>
                <td>Royalty Percentage:</td>
                <td><?php echo $traits['royalty_percentage'] . "%"; ?></td>
            </tr>
            <?php if ($traits['thumbnails']) { ?>
                <tr>
                    <td>Thumbnails:</td>
                    <td><?php echo $traits['thumbnail_size'][0] . "x" . $traits['thumbnail_size'][1]; ?></td>
                </tr>
            <?php } ?>
            <?php if ($traits['animation']) { ?>
                <tr>
                    <td>Animated:</td>
                    <td><?php echo $traits['animated_format']; ?></td>
            </tr>
            <?php } ?>
            <?php if ($traits['background_color']) { ?>
                <tr>
                    <td>Background Color:</td>
                    <td>Yes</td>
                </tr>
            <?php } ?>
            <?php if (isset($traits['seed'])) { ?>
                <tr>
                    <td>Generation Seed:</td>
                    <td><?php echo $traits['seed']; ?></td>
                </tr>
            <?php } ?>
            <tr>
                <td>Total Traits:</td>
                <td><?php echo $traits['trait_count']; ?></td>
            </tr>
        </table>
        <h3>Trait Details</h3>
        <table>
            <?php $l = 1; foreach ($traits['image_layers'] as $layer) {
                $name = $layer['layer_name'];
                $vars = $layer['variations'];
                echo '<tr>';
                echo "<th>Trait #${l}: ${name}</th>";
                echo "<th>Variations: ${vars}</th>";
                echo '</tr>';
                $v = 0; while ($v < $vars) {
                    $varname = array_keys($layer['filenames'])[$v];
                    $filename = $layer['filenames'][$varname];
                    $weight = $layer['weights'][$v];
                    $v = $v + 1;
                    echo '<tr>';
                    echo "<td>Variation #${v}: ${varname}</td>";
                    echo "<td>File: ${filename}<br />Weight: ${weight}</td>";
                    echo '</tr>';
                }
                $l = $l + 1;
            } ?>
        </table>
    <?php }

?>