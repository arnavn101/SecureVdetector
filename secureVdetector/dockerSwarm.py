import docker
from requests.exceptions import ReadTimeout


class InitDockerSwarm:
    """
    Initialize a Docker Swarm and create/manage services

    PARAMS:
        1) listCommands: list of bash commands to be run within the container
        2) imageName: docker image name (ubuntu, fedora, debian, etc)
        3) serviceName: default name of the service
        4) rPolicy: restart policy of docker containers (on-failure, always, unless-stopped, etc)
        5) memLimit: limits docker container's memory access in bytes
        6) cpuLimit: limits docker container's cpu access in units of 10^9 CPU shares
        7) netLimit: limits docker container's network bandwidth in KB
        8) listMountDirs: list of mount dirs which allows containers to access host files

    For more information on the docker API, refer to https://docker-py.readthedocs.io/en/stable/
    """
    def __init__(self, listCommands, imageName='ubuntu', serviceName='mySwarm', rPolicy='on-failure',
                 memLimit=2e9, cpuLimit=1e9, netLimit=100, listMountDirs=None):
        # Initialize docker client object and API
        self.dockerClient = docker.from_env()
        self.client_api = docker.APIClient(base_url='unix://var/run/docker.sock')

        # Avoid errors in which the node is already part of the swarm
        self.leaveDockerSwarm()

        # Start docker swarm & configure policies
        self.dockerClient.swarm.init()
        self.restart_policy = docker.types.RestartPolicy(condition=rPolicy)
        self.limitUsage = docker.types.Resources(mem_limit=int(memLimit), cpu_limit=int(cpuLimit))

        # Declare variables
        self.imageName = imageName
        self.listCommands = listCommands
        self.serviceName = serviceName
        self.netLimit = netLimit
        self.listMountDirs = listMountDirs

    def createBashCmd(self):
        initCmd = 'bash -c "'
        for indCommand in self.listCommands:
            initCmd += f'{indCommand} && '
        return initCmd[:-4] + '"'

    def runService(self, thisServiceName=None):
        if not thisServiceName:
            thisServiceName = self.serviceName
        # Run the docker service
        self.dockerClient.services.create(image=self.imageName, name=thisServiceName, command=self.createBashCmd(),
                                          mounts=self.listMountDirs, restart_policy=self.restart_policy,
                                          resources=self.limitUsage, tty=True)

    def getService(self):
        return self.dockerClient.services.get(self.serviceName)

    def getServiceJsonRepr(self):
        return self.getService().tasks()[0]

    def getServiceStatus(self):
        return self.getServiceJsonRepr()['Status']

    def getServiceState(self):
        return self.getServiceStatus()['State']

    def getServiceError(self):
        return self.getServiceStatus()['Err']

    def getContainerID(self):
        return self.getServiceStatus()['ContainerStatus']['ContainerID']

    def getContainerFsInfo(self):
        return next(filter(lambda ld: ld['Id'] == self.getContainerID(), self.client_api.df()['Containers']))

    def getContainer(self):
        return self.dockerClient.containers.get(self.getContainerID())

    def getContainerMemCpuInfo(self):
        return self.getContainer().stats(stream=False)

    def getLogsService(self):
        listLogs = list(self.getService().logs(stdout=True))
        return "".join(map(bytes.decode, listLogs))

    def removeService(self):
        self.getService().remove()

    def leaveDockerSwarm(self):
        # Ensure that the node leaves the swarm (manager nodes need to be forced)
        self.dockerClient.swarm.leave(force=True)

    def removeAllContainers(self):
        for indContainer in self.dockerClient.containers.list():
            try:
                indContainer.remove(force=True)
            except ReadTimeout:
                # During a forkbomb execution, there is sometimes a problem in removing a container
                # Source: https://github.com/docker/docker-py/issues/1374
                indContainer.kill(signal=9)

    def removeCurrentContainer(self):
        try:
            self.getContainer().remove(force=True)
        except ReadTimeout:
            self.getContainer().kill(signal=9)
