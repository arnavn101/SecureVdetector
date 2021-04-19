import math


# Convert input in bytes to appropriate format
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    ii = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, ii)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[ii])


# Handle data outputted by the NetHogs pipe
def handleNetHogsData(dataPipe):
    dataPipe = dataPipe.replace("\t", "   ").strip()
    listData = dataPipe.splitlines()
    formattedList = list(filter(lambda dt: len(dt.split()) == 3, listData))

    listInfo = []
    maxNetUsage = 0

    for element in formattedList:
        try:
            networkUsage = round(float(element.split()[-1]), 2)
        except Exception:
            continue
        listInfo.append(networkUsage)

    if len(listInfo) > 0:
        maxNetUsage = max(listInfo)
    return maxNetUsage


# Parse the Docker Memory API
def getMemUsage(inpList):
    return inpList['memory_stats']['max_usage'] / inpList['memory_stats']['limit']


# Parse the Docker CPU API
def getCpuUsage(inpList):
    systemDelta = inpList['cpu_stats']['system_cpu_usage'] - inpList['precpu_stats']['system_cpu_usage']
    cpuDelta = inpList['cpu_stats']['cpu_usage']['total_usage'] - inpList['precpu_stats']['cpu_usage'][
        'total_usage']
    return cpuDelta / systemDelta * len(inpList['cpu_stats']['cpu_usage']['percpu_usage'])
