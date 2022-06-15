from wxasync import WxAsyncApp, AsyncBind, AsyncShowDialogModal, StartCoroutine
import asyncio
import aiohttp
import re
import os
import subprocess
import wx
import time
import aiodocker
import docker
import webbrowser

IMAGE = "sk33z3r/loopygen"

# Checks condition(args) every interval until it is ture or until timeout seconds is elapsed
# Returns True if it timed out
async def wait_until(condition, interval=0.1, timeout=1, *args):
    start = time.time()
    timed_out = False
    while not condition(*args):
        await asyncio.sleep(interval)
        if time.time() - start >= timeout:
            timed_out = True
            break
    return timed_out


class MainWindow(wx.Frame):
    client: aiodocker.docker.Docker
    container: aiodocker.docker.DockerContainer
    container_image_id: str
    latest_image_id: str
    busy: bool

    DOCKER_PATHS_WIN = [r"C:\Program Files\Docker\Docker\Docker Desktop.exe"]

    def __init__(self, parent, title):
        self.client = None
        self.container = None
        self.container_image_id = None
        self.latest_image_id = None
        self.busy = True

        wx.Frame.__init__(self, parent, title=title)
        self.statusBar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)

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

        self.client = None
        StartCoroutine(self.initDocker, self)
        self.busy = False
        StartCoroutine(self.udpateUI, self)

    async def refreshDockerStatus(self):
        self.container = None
        self.container_image_id = None

        try:
            if not self.client:
                self.client = aiodocker.Docker()
        except docker.errors.DockerException as e:
            return

        containers = await self.client.containers.list(all=True, filters={})
        for ctnr in containers:
            if (await ctnr.show())["Name"] == "/loopygen":
                self.container = ctnr
                break

        # Read image ID from container
        try:
            self.container_image_id = await self.inspectContainer("Image")
            # print('current')
            # print(self.container_image_id)
        except Exception as e:
            print("Failed to check for updates:")
            print(e)

    async def udpateUI(self):
        while True:
            if not self.busy:
                await self.refreshButtons()
            await asyncio.sleep(1)

    async def refreshButtons(self):
        await self.refreshDockerStatus()

        if not self.client:
            self.startButton.Disable()
            self.startButton.SetLabel("Start LooPyGen")
            self.stopButton.Disable()
            self.updateButton.Disable()
            self.updateButton.SetLabel("LooPyGen is up-to-date")

        if (
            self.container
            and (await self.inspectContainer(["State", "Status"])) == "running"
        ):
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
        import platform

        self.statusBar.SetStatusText(f"Starting Docker Desktop...")

        res = await asyncio.create_subprocess_shell("docker ps")
        if res.returncode == 0:
            return True

        # Attempt to start
        if platform.system() == "Linux":
            # Linux
            await asyncio.create_subprocess_shell(
                "systemctl --user start docker-desktop"
            )
        elif platform.system() == "Darwin":
            # macOS
            await asyncio.create_subprocess_shell("open -a Docker")
        elif platform.system() == "Windows":
            # Windows
            import shutil

            docker_exe_path = shutil.which("docker.exe")
            if docker_exe_path:
                self.DOCKER_PATHS_WIN.insert(
                    0,
                    re.sub(
                        r"resources\\bin\\docker.exe",
                        r"Docker Desktop.exe",
                        docker_exe_path,
                        re.IGNORECASE,
                    ),
                )
            for potential_path in self.DOCKER_PATHS_WIN:
                if os.path.exists(potential_path):
                    subprocess.Popen(potential_path)
                    break
        else:
            print(f"Unknown platform {platform.system()}")
            return False

        # Wait for docker daemon to be up and running
        timed_out_waiting = await wait_until(
            lambda cmd: (
                await asyncio.create_subprocess_shell(cmd).returncode == 0 for _ in "_"
            ).__anext__(),
            3,
            30,
            "docker ps",
        )
        return not timed_out_waiting

    async def initDocker(self):
        if await self.ensureDockerDesktop():
            self.statusBar.SetStatusText(f"Docker Desktop started")
            await self.refreshDockerStatus()
        else:
            self.statusBar.SetStatusText(f"Could not start Docker Desktop")

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
                # print('latest')
                # print(self.latest_image_id)
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
            if (await AsyncShowDialogModal(dialog)) != wx.ID_OK:
                dialog.Destroy()
                return

            collection_dir = dialog.GetPath()
            dialog.Destroy()

        self.statusBar.SetStatusText(f"Getting docker image {IMAGE}...")
        loopygen_image = await self.client.images.pull(IMAGE)
        self.statusBar.SetStatusText(f"Starting new container loopygen...")
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

    def openUI(self):
        self.statusBar.SetStatusText("Opening LooPyGen UI...")
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
            self.statusBar.SetStatusText(f"Starting container {name}...")
            await self.container.start()
            just_started = True

        if self.container is None:
            self.busy = False
            return

        timed_out_waiting = await wait_until(
            lambda x: (
                await self.inspectContainer(["State", "Status"]) == "running"
                for _ in "_"
            ).__anext__(),
            1,
            10,
            None,
        )
        if timed_out_waiting:
            self.statusBar.SetStatusText(f"Could not start LooPyGen")
            self.busy = False
            return

        if just_started:
            await asyncio.sleep(2)

        self.openUI()
        self.busy = False

    async def onStopButton(self, event):
        self.busy = True
        print("stop", event)
        if (
            self.container
            and (await self.inspectContainer(["State", "Status"])) == "running"
        ):
            await self.container.kill()
            self.busy = False

    async def onUpdateButton(self, event):
        self.busy = True
        print("update", event)

        if self.container is None:
            self.busy = False
            return

        if (await self.inspectContainer(["State", "Status"])) == "running":
            name = await self.inspectContainer("Name")
            self.statusBar.SetStatusText(f"Stopping container {name}...")
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
        name = await self.inspectContainer("Name")
        self.statusBar.SetStatusText(f"Removing old container {name}...")
        await self.container.delete()
        await asyncio.sleep(2)
        self.statusBar.SetStatusText(f"Creating new container...")
        await self.createContainer(collection_dir)

        if self.container is None:
            self.busy = False
            return

        timed_out_waiting = await wait_until(
            lambda x: (
                await self.inspectContainer(["State", "Status"]) == "running"
                for _ in "_"
            ).__anext__(),
            1,
            10,
            None,
        )
        if timed_out_waiting:
            self.statusBar.SetStatusText(f"Could not start LooPyGen")
            self.busy = False
            return
        time.sleep(2)

        self.openUI()
        self.busy = False

    async def inspectContainer(self, branches=[]):
        if self.container is None:
            return None

        if isinstance(branches, str):
            branches = [branches]

        node = await self.container.show()
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
