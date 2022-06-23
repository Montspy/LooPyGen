# LooPyGen

![Release](https://badgen.net/github/release/sk33z3r/LooPyGen)
![Checks](https://badgen.net/github/checks/sk33z3r/LooPyGen)
![Issues](https://badgen.net/github/open-issues/sk33z3r/LooPyGen)

This is the unofficial Loopring Python Image Generator and Minter on Layer 2.

⚠️ **NEVER SHARE YOUR PRIVATE KEYS OR PASSPHRASES WITH ANYONE** ⚠️

Checkout the [Wiki pages](https://loopygen.ezl2.app) for up to date info on using the app!

Checkout the [issues section](https://github.com/sk33z3r/LooPyGen/issues) to report any problems, make feature requests, or keep up with our progress!

## LooPyGen CLI

The LooPyGen CLI client is run in Docker, but on-demand and headless as opposed to as a service through the GUI client. Below you will find a list the command reference, and how to pull the latest images and helper scripts.

**Notes**:

* You can clean up old images with: `docker image prune`
* Your config files are encrypted and stored in a Docker volume that is persistent on updates. Destroy the volume with: `docker volume prune`
* If you desire to access the shell of the container for any reason, do so with: `./loopygen-cli.sh bash`
* If you pass your config passphrase on the command line, it should be base64 encoded first. All transfer and mint commands accept this additional argument:
  ```shell
  --configpass $(echo -n "passphrase" | basenc --base64)
  ```

Download the script from GitHub with to your local working directory

```shell
# using wGET
$ wget -O ./loopygen-cli.sh https://github.com/sk33z3r/LooPyGen/blob/main/cli.sh && chmod +x loopygen-cli.sh
# using cURL
$ curl https://github.com/sk33z3r/LooPyGen/blob/main/cli.sh -o loopygen-cli.sh && chmod +x loopygen-cli.sh
```

Pull the latest image

```shell
$ ./loopygen-cli.sh update
```

Run a command

```shell
$ ./loopygen-cli.sh {command}
```

### Commands

Replace `{command}` with one of the below commands.

<details>
<summary>Show Config Commands</summary>

Encrypt your mint configuration

```shell
encrypt --mint
```

Encrypt your transfer configuration

```shell
encrypt --transfer
```

</details>

<details>
<summary>Show Image Generator Commands</summary>

Basic run:

```shell
generate --count XXX
```

Delete previously generated images before generating a new set:

```shell
generate --empty --count XXX
```

Start generating from a specific ID number:

```shell
generate --count XXX --id YY
```

If you have a beefy computer, you can try to generate images simultaneously to speed up the process:

```shell
generate --count XXX --threaded
```

</details>

<details>
<summary>Show Metadata Generator Commands</summary>

Basic run, after generating images:

```shell
metadata
```

Delete previously generated metadata before generating a new set:

```shell
metadata --empty
```

</details>

<details>
<summary>Show Minting Commands</summary>

Batch mint a collection:

```shell
mint --name <my_nft_collection> --amount 1
```

Mint a specific set of IDs:

```shell
mint --name <my_nft_collection> --start <startID> --end <endID> --amount 1
```

Mint a single CID:

```shell
mint --cid Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V --amount 100
```

Test run a mint (shows only what the script _would_ do, but doesn't actually do it):

```shell
mint --name <my_nft_collection> --testmint --amount 100
```

</details>

<details>
<summary>Show CID Calculator Commands</summary>

To scan CID files, input a path relative to your working directory.

The file must be at your current level or lower, and not outside of the directory. For instance, `../other-dir/somefile` would not work.

CIDv0:

```shell
cid ./relative/path/to/file
```

CIDv1:

```shell
cid --cid-version=1 ./relative/path/to/file
```
</details>
