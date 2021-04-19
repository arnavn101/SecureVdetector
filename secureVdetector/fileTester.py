import os
import time
from timeit import default_timer as timer
from secureVdetector import dockerSwarm
from secureVdetector import utils


class TestFile:
    """
    Test a linux-based file with Docker containers and analyze its behavior based on:
        - memory and cpu consumption
        - file i/o operations
        - network usage

    PARAMS:
        1) filePath: location of the file to be tested
        2) lDistro
        2) netLimit: limits docker container's network bandwidth in KB
        3) sleepForever: ensures that docker container continues to run after the file execution completes
        4) endAfter: ends the docker container after the desired time in seconds
    """
    def __init__(self, filePath, lDistro='ubuntu', netLimit=100, sleepForever=True, endAfter=60):
        # Declare Variables
        self.netLimit = netLimit
        self.filePath = filePath
        self.endAfter = endAfter
        self.listSysStatistics = []
        self.listNetStatistics = []

        # Init Docker Related vars
        listCmds = self.createListCmds()
        if sleepForever:
            listCmds.append('sleep infinity')
        thisPath = os.path.dirname(__file__)
        listMounts = [f'{os.path.dirname(thisPath)}:/tmp:rw']

        # Create & Run Docker Service
        self.thisDockerSwarm = dockerSwarm.InitDockerSwarm(listCmds, netLimit=netLimit, imageName=lDistro,
                                                           listMountDirs=listMounts)
        self.thisDockerSwarm.runService()

        # Run tests, conclusions, and results
        self.startTest()
        self.concludeTest()
        self.printResults()

    def startTest(self):
        # Get variables from Docker Swarm object
        dClient = self.thisDockerSwarm.dockerClient
        dAPI = self.thisDockerSwarm.client_api

        # Initialize Core Varibles
        toBreak = ['failed', 'complete']
        primContainerID = None
        netPIPE = 'openPipes/nethogs_pipe'

        # Start Timer and Looping
        startTime = timer()
        while self.thisDockerSwarm.getServiceState() not in toBreak:
            thisTime = timer()
            if (thisTime - startTime) > self.endAfter:
                break

            if os.path.exists(netPIPE):
                with open(netPIPE, 'r') as pipeFile:
                    dataPipe = pipeFile.read(100)
                    self.listNetStatistics.append(utils.handleNetHogsData(dataPipe))

            if 'ContainerStatus' in self.thisDockerSwarm.getServiceStatus():
                containerID = self.thisDockerSwarm.getContainerID()
                if not primContainerID:
                    primContainerID = containerID
                # If service has spawned another container, break the loop
                elif primContainerID != containerID:
                    break

                try:
                    memCpuStatsContainer = self.thisDockerSwarm.getContainerMemCpuInfo()
                    infoFsContainer = self.thisDockerSwarm.getContainerFsInfo()
                    self.listSysStatistics.append([memCpuStatsContainer, infoFsContainer])
                except IndexError:
                    pass

            time.sleep(1)

    def concludeTest(self):
        if 'Err' in self.thisDockerSwarm.getServiceStatus():
            errorCode = self.thisDockerSwarm.getServiceError()
            print(f'The container errored with the message: {errorCode}')

        listLogs = self.thisDockerSwarm.getLogsService()

        # Uncomment Line Below for Useful debug Info
        # print(listLogs)

        self.thisDockerSwarm.removeAllContainers()
        self.thisDockerSwarm.removeService()
        self.thisDockerSwarm.leaveDockerSwarm()

    def printResults(self):
        maxMemUsage = 0
        maxCpuUsage = 0
        maxSizeFS = 0
        maxNetUsage = 0

        # Get Max File storage Size
        listFSInfo = list(filter(lambda ld: 'SizeRw' in ld, list(zip(*self.listSysStatistics))[1]))
        if len(listFSInfo) > 0:
            maxSizeFS = max(map(lambda lList: lList['SizeRw'], listFSInfo))

        # Get Max Memory/CPU Usage
        listSystemInfo = list(filter(lambda ld: len(ld['memory_stats']) > 0, list(zip(*self.listSysStatistics))[0]))
        if len(listSystemInfo) > 0:
            maxMemUsage = max(map(lambda lList: utils.getMemUsage(lList), listSystemInfo))

        if len(listSystemInfo) > 0:
            maxCpuUsage = max(map(lambda lList: utils.getCpuUsage(lList), listSystemInfo))

        # Sometimes, the max cpu usage incorrectly becomes > 1
        if maxCpuUsage > 1:
            maxCpuUsage = 1

        if len(self.listNetStatistics) > 0:
            maxNetUsage = max(self.listNetStatistics)

        print(f"Max Memory Usage is {round(maxMemUsage, 2) * 100}%, Max CPU Usage is {round(maxCpuUsage, 2) * 100}%")
        print(f"Increase in Size of Filesystem: {utils.convert_size(maxSizeFS)}")
        print(f"Max Network Usage is {maxNetUsage} KB")

    def createListCmds(self):
        return ['dpkg -i /tmp/ubuntuDeps/downloadTrickle/*.deb',
                'dpkg -i /tmp/ubuntuDeps/downloadWget/*.deb',
                'dpkg -i /tmp/ubuntuDeps/downloadNethogs/*.deb',
                'dpkg -i /tmp/ubuntuDeps/downloadScreen/*.deb',
                'screen -d -m bash /tmp/scripts/nethogs.sh',
                f'trickle -d {self.netLimit} -u {self.netLimit} bash /tmp/{self.filePath}',
                ]
