from wxasync import WxAsyncApp, AsyncBind, StartCoroutine
import os
import wx
import sys
import time
import asyncio
import aiohttp
import aiodocker
import webbrowser

IMAGE = "sk33z3r/loopygen"

# Checks condition(args) every interval until it is ture or until timeout seconds is elapsed
# Returns True if it timed out
async def wait_until(condition, interval=0.1, timeout=1, *args):
    start = time.time()
    timed_out = False
    while not await condition(*args):
        await asyncio.sleep(interval)
        if time.time() - start >= timeout:
            timed_out = True
            break
    return timed_out


class MainWindow(wx.Frame):
    client: aiodocker.docker.Docker
    container: aiodocker.docker.DockerContainer
    status: str
    container_image_id: str
    latest_image_id: str
    busy: bool

    DOCKER_PATHS_WIN = [r"C:\Program Files\Docker\Docker\Docker Desktop.exe"]

    def __init__(self, parent, title):
        self.client = None
        self.container = None
        self.status = "exited"
        self.container_image_id = None
        self.latest_image_id = None
        self.busy = True

        wx.Frame.__init__(self, parent, title=title, style=style)

        icon = wx.EmptyIcon()
        if getattr(sys, 'frozen', False):
            icon.CopyFromBitmap(wx.Bitmap(os.path.join(sys._MEIPASS, "files/favicon.ico"), wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.statusBar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)

        self.buttonTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.refreshButtons, self.buttonTimer)

        self.startButton = wx.Button(self.panel, wx.ID_ANY, "Open LooPyGen UI")
        self.stopButton = wx.Button(self.panel, wx.ID_ANY, "Stop LooPyGen")
        self.updateButton = wx.Button(self.panel, wx.ID_ANY, "LooPyGen is up-to-date")
        AsyncBind(wx.EVT_BUTTON, self.onStartButton, self.startButton)
        AsyncBind(wx.EVT_BUTTON, self.onStopButton, self.stopButton)
        AsyncBind(wx.EVT_BUTTON, self.onUpdateButton, self.updateButton)

        grid = wx.BoxSizer(wx.HORIZONTAL)
        grid.Add(self.startButton, 0, wx.ALL, 5)
        grid.Add(self.stopButton, 0, wx.ALL, 5)
        grid.Add(self.updateButton, 0, wx.ALL, 5)

        self.panel.SetSizer(grid)
        grid.Fit(self)

        self.startButton.Disable()
        self.stopButton.Disable()
        self.updateButton.Disable()

        StartCoroutine(self.initDocker, self)
        self.buttonTimer.Start(500)

    def setStatusBarMessage(self, message):
        if self.busy:
            message = "Busy: " + message
        self.statusBar.SetStatusText(message)

    async def getContainerByName(self, name):
        containers = await self.client.containers.list(all=True, filters={})
        for ctnr in containers:
            # print((await ctnr.show())["Name"])
            if (await ctnr.show())["Name"] == "/" + name:
                return ctnr
        return None

    async def refreshDockerStatus(self):
        try:
            if not self.client:
                self.client = aiodocker.Docker()
        except Exception as e:
            self.client = None
            return

        if not self.client:
            return

        self.container = await self.getContainerByName("loopygen")

        if self.container:
            self.status = await self.inspectContainer(["State", "Status"])

        # Read image ID from container
        try:
            self.container_image_id = await self.inspectContainer("Image")
        except Exception as e:
            print("Failed to check for updates:")
            print(e)

    async def updateUI(self):
        while True:
            if not self.busy:
                await self.refreshDockerStatus()
            await asyncio.sleep(1)

    def refreshButtons(self, event):
        if self.busy:
            self.startButton.Disable()
            self.stopButton.Disable()
            self.updateButton.Disable()
            return

        if not self.client:
            self.startButton.Disable()
            self.startButton.SetLabel("Start LooPyGen")
            self.stopButton.Disable()
            self.updateButton.Disable()
            self.updateButton.SetLabel("LooPyGen is up-to-date")

        if self.container and self.status == "running":
            self.startButton.Enable()
            self.startButton.SetLabel("Open LooPyGen UI")
            self.stopButton.Enable()
        else:
            self.startButton.Enable()
            self.startButton.SetLabel("Start LooPyGen")
            self.stopButton.Disable()

        if (
            self.container_image_id
            and self.latest_image_id
            and self.container_image_id != self.latest_image_id
        ):
            self.updateButton.Enable()
            self.updateButton.SetLabel("Update LooPyGen")
        else:
            self.updateButton.Disable()
            self.updateButton.SetLabel("LooPyGen is up-to-date")

    async def ensureDockerDesktop(self):
        import shutil
        import platform

        was_detected = False

        proc = await asyncio.create_subprocess_shell("docker ps")
        returncode = await proc.wait()
        if returncode == 0:
            print("Docker Desktop is running")
            return True

        this_os = platform.system()
        if this_os == "Darwin":
            this_os = "macOS"
        self.setStatusBarMessage(f"Starting Docker Desktop for {this_os}...")

        # Attempt to start
        if platform.system() == "Linux":
            # Linux
            proc = await asyncio.create_subprocess_shell(
                "systemctl --user start docker-desktop",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            print(stdout)
            print(stderr)
            if proc.returncode == 0:
                was_detected = True
        elif platform.system() == "Darwin":
            # macOS
            proc = await asyncio.create_subprocess_shell(
                "open -a Docker",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            print(stdout)
            print(stderr)
            if proc.returncode == 0:
                was_detected = True
        elif platform.system() == "Windows":
            # Windows
            docker_exe_path = shutil.which("docker.exe")
            if docker_exe_path:
                self.DOCKER_PATHS_WIN.insert(
                    0,
                    docker_exe_path.replace(
                        r"resources\bin\docker.exe", r"Docker Desktop.exe"
                    ),
                )
            for potential_path in self.DOCKER_PATHS_WIN:
                if os.path.exists(potential_path):
                    print(f"Found Docker Desktop at {potential_path}")
                    os.spawnl(os.P_NOWAIT, potential_path, potential_path)
                    was_detected = True
                    break
        else:
            print(f"Unknown platform {platform.system()}")
            return False

        if not was_detected:
            self.setStatusBarMessage(
                "Failed to start Docker Desktop. Please install Docker Desktop and restart the app."
            )
            webbrowser.open("https://www.docker.com/products/docker-desktop/")
            return False

        # Wait for docker daemon to be up and running
        print("Waiting for Docker daemon to be up and running...")
        self.setStatusBarMessage("Waiting for Docker Desktop to start...")
        timed_out_waiting = await wait_until(
            lambda cmd: (
                await (await asyncio.create_subprocess_shell(cmd)).wait() == 0
                for _ in "_"
            ).__anext__(),
            0.5,
            30,
            "docker ps",
        )

        if timed_out_waiting:
            print("Timed out waiting for Docker daemon to start")
            self.setStatusBarMessage(
                "Failed to start Docker Desktop. Please install Docker Desktop and restart the app."
            )
            webbrowser.open("https://www.docker.com/products/docker-desktop/")
            return False
        else:
            self.setStatusBarMessage("Docker Desktop started successfully")
            return True

    async def initDocker(self):
        if await self.ensureDockerDesktop():
            self.busy = False
            self.setStatusBarMessage(f"Docker Desktop started")
            await self.refreshDockerStatus()
            StartCoroutine(self.updateUI, self)

        # Get image ID of latest from Docker hub
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"https://auth.docker.io/token?scope=repository:{IMAGE}:pull&service=registry.docker.io"
                )
                token = (await resp.json())["token"]
                resp = await session.get(
                    f"https://registry.hub.docker.com/v2/{IMAGE}/manifests/latest",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
                    },
                )
                self.latest_image_id = (await resp.json())["config"]["digest"]
                # print("latest_image_id", self.latest_image_id)
        except Exception as e:
            print("Failed to check for updates:")
            print(e)

    async def createContainer(self, collection_dir: str = None):
        if not collection_dir:
            dialog = wx.DirDialog(
                self,
                "Select your collections directory:",
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
            )
            if (dialog.ShowModal()) != wx.ID_OK:
                dialog.Destroy()
                return

            collection_dir = dialog.GetPath()
            dialog.Destroy()

        self.setStatusBarMessage(f"Downloading new docker image {IMAGE}...")
        loopygen_image = await self.client.images.pull(IMAGE)
        self.setStatusBarMessage(f"Starting new container loopygen...")
        self.container = await self.client.containers.run(
            {
                "Image": IMAGE,
                "HostConfig": {
                    "Binds": [f"{collection_dir}:/loopygen/collections:rw"],
                    "PortBindings": {
                        "80/tcp": [{"HostPort": "8080"}],
                    },
                },
            },
            name="loopygen",
        )

    async def isUIRunning(self):
        async with aiohttp.ClientSession() as session:
            try:
                resp = await session.get(f"http://localhost:8080/", timeout=0.9)
                return resp.status == 200
            except Exception as e:
                return False

    def openUI(self):
        webbrowser.open("http://localhost:8080/")

    async def onStartButton(self, event):
        self.busy = True
        print("start", event)
        just_started = False

        if self.container is None:
            await self.createContainer()
            just_started = True
        elif (await self.inspectContainer(["State", "Status"])) != "running":
            name = await self.inspectContainer("Name")
            self.setStatusBarMessage(f"Starting container {name}...")
            await self.container.start()
            just_started = True

        if self.container is None:
            self.busy = False
            self.setStatusBarMessage("Could not start LooPyGen")
            return

        timed_out_waiting = await wait_until(
            lambda x: (await self.isUIRunning() for _ in "_").__anext__(),
            1,
            40,  # 10s for docker to start, 30s for PHP to serve
            None,
        )
        if timed_out_waiting:
            self.busy = False
            self.setStatusBarMessage("Could not start LooPyGen")
            return

        self.openUI()
        self.busy = False
        self.setStatusBarMessage("Opening LooPyGen UI")

    async def onStopButton(self, event):
        self.busy = True
        print("stop", event)
        if (
            self.container
            and (await self.inspectContainer(["State", "Status"])) == "running"
        ):
            await self.container.kill()
        self.busy = False
        self.setStatusBarMessage("LooPyGen stopped")

    async def onUpdateButton(self, event):
        self.busy = True
        print("update", event)

        if self.container is None:
            self.busy = False
            self.setStatusBarMessage("Failed to update LooPyGen")
            return

        if (await self.inspectContainer(["State", "Status"])) == "running":
            name = await self.inspectContainer("Name")
            self.setStatusBarMessage(f"Stopping container {name}...")
            await self.container.kill()
            await wait_until(
                lambda x: (
                    await self.inspectContainer(["State", "Status"]) == "exited"
                    for _ in "_"
                ).__anext__(),
                1,
                10,
                None,
            )

        # Get collections path from existing container
        collection_dir = await self.inspectContainer(["Mounts", 0, "Source"])

        # Delete old backup container
        old_container = await self.getContainerByName("old-loopygen")
        if old_container:
            name = await self.inspectContainer("Name", old_container)
            self.setStatusBarMessage(f"Removing old container {name}...")
            await old_container.remove()

        # Move existing container to backup container
        name = await self.inspectContainer("Name")
        self.setStatusBarMessage(f"Moving outdated container {name} to old-loopygen...")
        await self.container.rename("old-loopygen")
        await asyncio.sleep(2)

        # Create new container
        self.setStatusBarMessage(f"Creating new container...")
        await self.createContainer(collection_dir)

        if self.container is None:
            self.busy = False
            self.setStatusBarMessage("Failed to update LooPyGen")
            return

        timed_out_waiting = await wait_until(
            lambda x: (await self.isUIRunning() for _ in "_").__anext__(),
            1,
            40,  # 10s for docker to start, 30s for PHP to serve
            None,
        )
        if timed_out_waiting:
            self.busy = False
            self.setStatusBarMessage(f"Could not start LooPyGen")
            return
        await asyncio.sleep(2)

        self.openUI()
        self.busy = False
        self.setStatusBarMessage("Opening LooPyGen UI")

    async def inspectContainer(self, branches=[], container=None):
        if container is None:
            container = self.container
        if container is None:
            return None

        if isinstance(branches, str):
            branches = [branches]

        node = await container.show()
        for b in branches:
            node = node[b]

        return node


async def main():
    app = WxAsyncApp(False)
    frame = MainWindow(None, "LooPyGen Companion")
    frame.Show()
    await app.MainLoop()
    if frame.client:
        await frame.client.close()


asyncio.run(main())
