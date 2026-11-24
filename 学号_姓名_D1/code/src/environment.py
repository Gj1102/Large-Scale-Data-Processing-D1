import ctypes,json,os,platform,sys,torch,torchvision
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),('ullAvailExtendedVirtual',ctypes.c_ulonglong)]
m=MEMORYSTATUSEX(); m.dwLength=ctypes.sizeof(m); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
print(json.dumps({'platform':platform.platform(),'processor':platform.processor(),'logical_cpus':os.cpu_count(),'memory_gib':round(m.ullTotalPhys/1024**3,2),'python':sys.version,'torch':torch.__version__,'torchvision':torchvision.__version__,'cuda':torch.cuda.is_available(),'backend':'Gloo','world_size':2,'OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS')},indent=2))
