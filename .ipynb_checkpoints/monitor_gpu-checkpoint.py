import pynvml
import time

pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # 첫 번째 GPU 선택

for i in range(100):
    # GPU 사용률 측정
    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
    print(f" [+]  {i:04d}  GPU 사용률 / 메모리 사용률: {utilization.gpu}% / {utilization.memory}% ")
    time.sleep(0.5)


pynvml.nvmlShutdown()