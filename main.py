import asyncio
from playwright.async_api import async_playwright

import os
import time
from datetime import datetime
import json
import nest_asyncio
import argparse

import pynvml

nest_asyncio.apply()


os.environ["__NV_PRIME_RENDER_OFFLOAD"] = "1"
os.environ["__GLX_VENDOR_LIBRARY_NAME"] = "nvidia"


# GPU 측정 초기화
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # 첫 번째 GPU 선택




async def get_page_info(page=None):  
    # GPU 가속 상태 확인
    if page:
        gpu_info = await page.evaluate("""() => {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            
            if (!gl) {
                return { gpuAccelerated: false, reason: 'WebGL not supported' };
            }
            
            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'Unknown';
            const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'Unknown';
            
            return {
                gpuAccelerated: true,
                vendor: vendor,
                renderer: renderer,
                webglVersion: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                extensions: gl.getSupportedExtensions()
            };
        }""")
        
        # GPU 정보 저장
        with open('gpu_info.json', 'w') as f:
            json.dump(gpu_info, f, indent=2)
                
        # 추가적인 브라우저 정보
        browser_info = await page.evaluate("""() => {
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory || 'Not available'
            };
        }""")
    
        with open('browser_info.json', 'w') as f:
            json.dump(browser_info, f, indent=2)
    
    
        return gpu_info, browser_info
    else:
        raise "No Page Instance"
        return False

    
async def capture_screenshot_with_gpu(url, output_path, enable_gpu=True, repeat=1):
    
    async with async_playwright() as p:
        
        
        # GPU 가속 플래그 설정
        # gpu_flags = [
        #     '--enable-gpu-rasterization',
        #     '--ignore-gpu-blocklist',
        #     '--enable-webgl',
        #     '--use-gl=angle',
        #     '--use-angle=metal',
        # ]

        gpu_flags = [
            '--ignore-gpu-blocklist',  # GPU 블랙리스트 무시
            '--enable-gpu-rasterization',  # GPU 래스터화 활성화
            '--enable-raw-draw',  # 성능 개선
            '--use-angle=egl',  # macOS: 'metal', Linux: 'gl-egl'
            '--enable-features=Vulkan,SharedArrayBuffer',
            '--headless=new'  # 새로운 헤드리스 모드 사용
            '--disable-gpu-sandbox',
        ]
                
        no_gpu_flags = [
            '--disable-gpu',                   # GPU 하드웨어 가속 비활성화
            '--disable-gpu-compositing',       # GPU 컴포지팅 비활성화
            '--disable-gpu-rasterization',     # GPU 래스터화 비활성화
            '--disable-software-rasterizer',   # 소프트웨어 래스터라이저 비활성화
            '--disable-webgl',                 # WebGL 비활성화
        ]        
        
        # 브라우저 실행
        browser = await p.chromium.launch(
            headless=True,
            args= gpu_flags if enable_gpu else no_gpu_flags,
            chromium_sandbox=False
        )

        start_time = time.time()
        
        context = await browser.new_context(
            is_mobile=False,
            has_touch=False,
            # javascript_enabled=True,
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        # 웹사이트 방문
        await page.goto(url)
        time.sleep(0.5)

        for i in range(0,repeat):
            # print(f" - screenshot: {i}")
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            print(f" [+]   GPU 사용률 / 메모리 사용률: {utilization.gpu}% / {utilization.memory}% ")
            await page.screenshot(path=output_path, full_page=True)


        end_time = time.time()
        duration = end_time - start_time
        # GPU 가속 상태 확인
        gpu_info, browser_info = await get_page_info(page)

        
        # GPU 사용률 측정
        utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
        print(f" [+]   GPU 사용률 / 메모리 사용률: {utilization.gpu}% / {utilization.memory}% ")

        # WebGL 지원 페이지에서 렌더러 정보 추출
        await page.goto("https://webglreport.com/")
        renderer = await page.evaluate('''() => {
            const gl = document.createElement('canvas').getContext('webgl');
            return gl.getParameter(gl.RENDERER);
        }''')
        print(f" -------> WebGL Renderer: {renderer}")  # NVIDIA GPU명이 출력되면 성공


        
        await browser.close()
        
        return gpu_info, browser_info, duration

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Capture website screenshot with GPU acceleration")
    parser.add_argument("--url", help="URL to capture (e.g., https://www.example.com)", default="https://webglsamples.org/aquarium/aquarium.html")
    parser.add_argument("--output", help="Output filename for the screenshot", default="screenshot.png")
    parser.add_argument("--enable_gpu", action="store_true", help="GPU 가속화 활성화 (기본값: 비활성화)")
    parser.add_argument("--repeat", type=int, default=1, help="스크린샷을 캡처할 반복 횟수 (기본값: 1)")

    args = parser.parse_args()

    url = args.url
    output_path = args.output
    enable_gpu = args.enable_gpu
    repeat = args.repeat

        
    # 프로토콜 검사 및 추가
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        print(f"프로토콜이 없어 'https://'를 추가했습니다. URL: {url}")
        
    try:
        # 스크린샷 캡처 실행
        gpu_info, browser_info, duration = asyncio.run(capture_screenshot_with_gpu(url, output_path, enable_gpu, repeat=repeat))
        print(f"스크린샷이 성공적으로 저장되었습니다. with GPU : {enable_gpu} ")
        print("GPU 정보:\n", gpu_info)
        print("Browser 정보:\n", browser_info)
        print(f" Duration {duration:0.2f} Sec.")
        
    except Exception as e:
        print(f"에러 발생: {e}")
        
    pynvml.nvmlShutdown()
    
    