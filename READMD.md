# Playwright를 이용한 스크린샷 (GPU Enabled)
- Playwright를 이용하여 Screenshot을 수행합니다.
- 단, WebGL을 사용하는 웹앱을 스크린샷하기 위해서는 GPU Enable이 필요합니다.
- AWS g5.xlarge 등 Nividia-GPU를 탑재한 Linux Server / CLI 환경에서 Screenshot을 수행하기 위함입니다.

# 설치
- `pip install -r requirements.txt`
- cli에서 `playwright install` 실행
  
> 만약 디펜던시 등으로 설치가 잘 안되면
> `playwright install-deps` 설치


# 빠른 실행
- gpu mode : `python main.py --enable_gpu --output screenshot_gpu.png`
- no gpu mode : `python main.py --output screenshot_no_gpu.png`

## 실행 옵션
- `--url` : 테스트 url 주소
- `--output` : 스크린샷 이미지 
- `--enable_gpu` : GPU 활성화 여부
- `--repeat` : 반복 실행 횟수 (현재 그다지 필요 없음)


# Playwright 설정

## GPU Enabled 설정 (Linux / MacOS )

```
gpu_flags = [
            '--enable-gpu-rasterization',
            '--ignore-gpu-blocklist',
            '--enable-webgl',
            '--use-gl=angle',
            '--use-angle=metal',
        ]
```

## GPU Disabled 설정

```
no_gpu_flags = [
            '--disable-gpu',                   # GPU 하드웨어 가속 비활성화
            '--disable-gpu-compositing',       # GPU 컴포지팅 비활성화
            '--disable-gpu-rasterization',     # GPU 래스터화 비활성화
            '--disable-software-rasterizer',   # 소프트웨어 래스터라이저 비활성화
            '--disable-webgl',                 # WebGL 비활성화
        ]    
```


## GPU 활성화 확인

browser가 설치되어 있는 Client 경우는 browser를 오픈하여, 


그러나, Server에서 Script로 동작하는 경우는 이 방법으로 확인 할 수 없다. 
따라서, 다음과 같이 javascript 에서 `canvas` element를 생성하고, webgl를 직접 호출하여 확인 할 수 있다. 
```
gl = canvas.getContext("experimental-webgl");
if(!gl) {
    alert("Your browser does not support WebGL");
}
```

이 부분을 반영하여 소스코드에서는 다음과 같이 처리하여, WebGL 여부를 확인 한다. 

```
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
```

### GPU 활성화 확인 (실패 방법들)
- `chrome://gpu` 확인은 UI가 있는 브라우저에서만 확인이 가능하다.
- 즉, playwright를 headless로 실행한 경우 확인이 안된다는 것이다.
- 참조 : https://github.com/microsoft/playwright/issues/15533
- linux에서 headless=False로 브라우저를 띄우려면 X11 등 X-Server가 설치 되어 있어야 한다.

