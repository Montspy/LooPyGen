from pprint import pprint
import re
import os
import subprocess
import sys
import requests
import wx
import time
import json
import docker
import webbrowser

IMAGE = "sk33z3r/loopygen"


def wait_until(condition, interval=0.1, timeout=1, *args):
    start = time.time()
    while not condition(*args) and time.time() - start < timeout:
        time.sleep(interval)


class MainWindow(wx.Frame):
    client: docker.DockerClient
    api_client: docker.APIClient
    container: docker.models.containers.Container
    container_image_id: str
    latest_image_id: str

    def __init__(self, parent, title):
        self.latest_image_id = None
        self.initDocker()

        wx.Frame.__init__(self, parent, title=title)
        self.statusBar = self.CreateStatusBar()
        self.panel = wx.Panel(self, wx.ID_ANY)

        self.pollTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.pollTimer)

        self.startButton = wx.Button(self.panel, wx.ID_ANY, "Start LooPyGen")
        self.stopButton = wx.Button(self.panel, wx.ID_ANY, "Stop LooPyGen")
        self.updateButton = wx.Button(self.panel, wx.ID_ANY, "LooPyGen is up-to-date")
        self.Bind(wx.EVT_BUTTON, self.onStartButton, self.startButton)
        self.Bind(wx.EVT_BUTTON, self.onStopButton, self.stopButton)
        self.Bind(wx.EVT_BUTTON, self.onUpdateButton, self.updateButton)

        grid = wx.BoxSizer(wx.HORIZONTAL)
        grid.Add(self.startButton, 0, wx.ALL, 5)
        grid.Add(self.stopButton, 0, wx.ALL, 5)
        grid.Add(self.updateButton, 0, wx.ALL, 5)

        self.panel.SetSizer(grid)
        grid.Fit(self)

        self.startButton.Disable()
        self.stopButton.Disable()
        self.updateButton.Disable()
        self.refreshButtons()
        self.pollTimer.Start(1000)

        # self.client.containers.run(
        #     "sk33z3r/loopygen:dev-sk33z3r",
        #     detach=True,
        #     name="loopygen",
        #     ports={80: 8080},
        #     volumes=[f"C:\\Users\\Valentin\\Desktop\\collections:/loopygen/collections"],
        # )
        # sys.exit()

        if not self.client:
            self.startDocker()

    def refreshDockerStatus(self):
        self.client = None
        self.api_client = None
        self.container = None
        self.container_image_id = None

        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient(os.getenv("DOCKER_HOST"))
        except docker.errors.DockerException as e:
            return

        containers = self.client.containers.list(all=True)
        containers = list(filter(lambda ctnr: "loopygen" in ctnr.name, containers))
        if len(containers) == 0:
            self.container = None
            return
        self.container = containers[0]

        # Read image ID from container
        try:
            self.container_image_id = self.api_client.inspect_container(
                self.container.id
            )["Image"]
        except Exception as e:
            print("Failed to check for updates:")
            print(e)

        # print(self.container_image_id)

    def onTimer(self, event):
        self.refreshButtons()

    def refreshButtons(self):
        self.refreshDockerStatus()

        if not self.client:
            self.startButton.Disable()
            self.stopButton.Disable()
            self.updateButton.Disable()
            self.updateButton.SetLabel("LooPyGen is up-to-date")

        if self.container and self.container.status == "running":
            self.startButton.Disable()
            self.stopButton.Enable()
        else:
            self.startButton.Enable()
            self.stopButton.Disable()

        if (
            self.container_image_id
            and self.latest_image_id
            and self.container_image_id != self.latest_image_id
        ):
            self.updateButton.Enable()
            self.updateButton.SetLabel("Update LooPyGen")
            self.statusBar.SetStatusText(
                f"New {IMAGE} update found: {self.latest_image_id}"
            )
        else:
            self.updateButton.Disable()
            self.updateButton.SetLabel("LooPyGen is up-to-date")

    def initDocker(self):
        self.refreshDockerStatus()

        # Get image ID of latest from Docker hub
        try:
            token = json.loads(
                requests.get(
                    f"https://auth.docker.io/token?scope=repository:{IMAGE}:pull&service=registry.docker.io"
                ).text
            )["token"]
            self.latest_image_id = json.loads(
                requests.get(
                    f"https://registry.hub.docker.com/v2/{IMAGE}/manifests/latest",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
                    },
                ).text
            )["config"]["digest"]
            # print(self.latest_image_id)
        except Exception as e:
            print("Failed to check for updates:")
            print(e)

    def createContainer(self, collection_dir: str = None):
        if not collection_dir:
            dialog = wx.DirDialog(
                self,
                "Select your collections directory:",
                style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
            )
            if dialog.ShowModal() != wx.ID_OK:
                dialog.Destroy()
                return

            dialog.Destroy()
            collection_dir = dialog.GetPath()

        self.statusBar.SetStatusText(f"Getting docker image {IMAGE}...")
        loopygen_image = self.client.images.pull(IMAGE)
        self.statusBar.SetStatusText(f"Starting new container loopygen...")
        self.container = self.client.containers.run(
            loopygen_image,
            detach=True,
            name="loopygen",
            ports={80: 8080},
            volumes=[f"{collection_dir}:/loopygen/collections"],
        )

    def openUI(self):
        if not self.container:
            return

        wait_until(
            lambda ctnr: ctnr.reload() or ctnr.status == "running",
            1,
            10,
            self.container,
        )
        self.statusBar.SetStatusText("Opening LooPyGen UI...")
        time.sleep(2)
        webbrowser.open("http://localhost:8080/")
        self.statusBar.SetStatusText("LooPyGen started")

    def onStartButton(self, event):
        print("start", event)

        if not self.container:
            self.createContainer()
        else:
            self.statusBar.SetStatusText(f"Starting container {self.container.name}...")
            self.container.start()

        self.openUI()

    def onStopButton(self, event):
        print("stop", event)
        if self.container and self.container.status == "running":
            self.container.stop()

    def onUpdateButton(self, event):
        print("update", event)

        if not self.container:
            return

        if self.container.status == "running":
            self.statusBar.SetStatusText(f"Stopping container {self.container.name}...")
            self.container.stop()
            wait_until(
                lambda ctnr: ctnr.reload() or ctnr.status == "exited",
                1,
                10,
                self.container,
            )

        # Get collections path from existing container
        mounts = self.api_client.inspect_container(self.container.id)["Mounts"]
        collection_dir = mounts[0]["Source"]
        self.statusBar.SetStatusText(f"Removing old container {self.container.name}...")
        self.container.remove()
        time.sleep(2)
        self.statusBar.SetStatusText(f"Creating new container...")
        print(collection_dir)
        self.createContainer(collection_dir)

        self.openUI()


app = wx.App(False)
frame = MainWindow(None, "LooPyGen Companion").Show()
app.MainLoop()
