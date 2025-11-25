# ASR Service API 文档

**服务地址**: `http://106.55.166.12:8001`

---

## HTTP 端点

### 1. 健康检查

**GET** `/health`

检查服务是否正常运行。

**响应示例**:
```json
{
  "status": "healthy",
  "service": "ASR Service",
  "version": "1.0.0"
}
```

---

### 2. 文件上传转写

**POST** `/asr/transcribe`

上传音频文件进行转写。

**请求参数**:
- `file` (文件): 音频文件（支持 MP3, WAV, M4A 等格式）
- `language` (表单字段, 可选): 语言代码
  - `zh`: 中文
  - `en`: 英文
  - `auto`: 自动检测（默认）

**响应示例**:
```json
{
  "text": "你好，这是一段测试语音",
  "language": "zh",
  "confidence": null
}
```

**curl 示例**:
```bash
curl -X POST "http://106.55.166.12:8001/asr/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=auto"
```

---

### 3. 切换ASR模型

**POST** `/asr/switch_model`

动态切换Whisper模型大小。

**请求参数** (JSON):
- `model_name` (必填): 模型名称
  - `tiny`: 最快，准确度较低
  - `base`: 快速，准确度一般
  - `small`: 平衡
  - `medium`: 较慢，准确度高
  - `large`: 最慢，准确度最高
- `device` (可选): 运行设备（`cpu` 或 `cuda`）

**响应示例**:
```json
{
  "status": "success",
  "message": "Switched to model: medium",
  "device": "cpu"
}
```

---

### 4. 获取模型信息

**GET** `/asr/info`

获取当前使用的ASR模型信息。

**响应示例**:
```json
{
  "model_type": "whisper",
  "model_name": "base",
  "device": "cpu"
}
```

---

## WebSocket 端点

### 流式语音识别（重点）

**WebSocket** `/asr/stream`

实时流式语音识别，支持智能分句和自动会话结束。

#### 功能特性

- ✅ 实时语音识别，无需等待完整音频
- ✅ 智能两级停顿检测：
  - **500ms 停顿** → 句子结束（转写并继续监听）
  - **1500ms 停顿** → 会话结束（转写并停止录音）
- ✅ 可配置的VAD参数（灵敏度、最小语音长度等）
- ✅ 自动过滤噪音和空白音频
- ✅ 支持中英文自动识别

---

#### 连接流程

```
1. 客户端连接 WebSocket
   ↓
2. [可选] 客户端发送 VAD 配置
   ↓
3. 客户端流式发送音频数据（16kHz PCM）
   ↓
4. 服务端实时返回状态更新
   ↓
5. 检测到停顿 → 转写并返回结果
   ↓
6. 1.5秒无声 → 自动结束会话
```

---

#### 音频格式要求

| 参数 | 值 |
|------|-----|
| 采样率 | 16000 Hz |
| 声道数 | 1 (单声道) |
| 位深度 | 16-bit (int16) |
| 编码格式 | PCM |
| 传输格式 | Base64 编码的字符串 |

---

#### 消息格式

##### 客户端 → 服务端

**1. 配置 VAD 参数（可选）**

```json
{
  "type": "config",
  "config": {
    "threshold": 0.6,
    "min_speech_duration_ms": 400,
    "min_silence_for_sentence_ms": 500,
    "min_silence_for_session_ms": 1500
  }
}
```

**参数说明**:
- `threshold` (0.3-0.9): 语音检测阈值，越高越不敏感（默认 0.6）
- `min_speech_duration_ms` (100-1000): 最小有效语音时长（默认 400ms）
- `min_silence_for_sentence_ms` (300-1000): 句子结束的停顿时长（默认 500ms）
- `min_silence_for_session_ms` (1000-3000): 会话结束的停顿时长（默认 1500ms）

**2. 发送音频数据**

```json
{
  "type": "audio",
  "data": "SGVsbG8gV29ybGQ="
}
```

- `data`: Base64 编码的 PCM 音频数据（16kHz, mono, int16）

**3. 重置 VAD 状态**

```json
{
  "type": "reset"
}
```

---

##### 服务端 → 客户端

**1. 配置确认**

```json
{
  "type": "config_ack",
  "config": {
    "threshold": 0.6,
    "min_speech_duration_ms": 400,
    "min_silence_for_sentence_ms": 500,
    "min_silence_for_session_ms": 1500
  }
}
```

**2. 状态更新**

```json
{
  "type": "status",
  "status": "speaking"
}
```

- `status` 可能的值:
  - `speaking`: 正在说话
  - `transcribing`: 正在转写

**3. 转写结果**

```json
{
  "type": "result",
  "text": "你好，这是第一句话",
  "language": "zh",
  "session_ended": false
}
```

- `text`: 转写文本
- `language`: 检测到的语言（`zh` 或 `en`）
- `session_ended`: 是否会话结束
  - `false`: 句子结束，继续监听下一句
  - `true`: 会话结束，客户端应停止录音

**4. 会话结束（无音频）**

```json
{
  "type": "session_end",
  "message": "Session ended due to prolonged silence"
}
```

当会话结束但没有音频需要转写时发送（例如：转写后再静音1秒）。

**5. 错误消息**

```json
{
  "type": "error",
  "message": "错误描述"
}
```

---

#### JavaScript 示例代码

```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://106.55.166.12:8001/asr/stream');

// 1. 连接成功后发送配置（可选）
ws.onopen = () => {
  console.log('WebSocket 已连接');

  // 发送 VAD 配置
  ws.send(JSON.stringify({
    type: 'config',
    config: {
      threshold: 0.6,
      min_speech_duration_ms: 400,
      min_silence_for_sentence_ms: 500,
      min_silence_for_session_ms: 1500
    }
  }));
};

// 2. 处理服务端消息
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'config_ack':
      console.log('配置已确认:', message.config);
      break;

    case 'status':
      console.log('状态:', message.status);
      break;

    case 'result':
      console.log('转写结果:', message.text);
      console.log('语言:', message.language);

      if (message.session_ended) {
        console.log('会话结束，停止录音');
        stopRecording();
        ws.close();
      }
      break;

    case 'session_end':
      console.log('会话结束（无转写）');
      stopRecording();
      ws.close();
      break;

    case 'error':
      console.error('错误:', message.message);
      break;
  }
};

// 3. 发送音频数据
function sendAudioChunk(audioBuffer) {
  // audioBuffer 应该是 Int16Array 格式的 PCM 数据
  const base64Audio = btoa(
    String.fromCharCode(...new Uint8Array(audioBuffer.buffer))
  );

  ws.send(JSON.stringify({
    type: 'audio',
    data: base64Audio
  }));
}

// 4. 使用 MediaRecorder 捕获麦克风音频
async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      sampleRate: 16000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    }
  });

  const audioContext = new AudioContext({ sampleRate: 16000 });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);

  processor.onaudioprocess = (e) => {
    const inputData = e.inputBuffer.getChannelData(0);
    const pcmData = new Int16Array(inputData.length);

    // 转换 float32 到 int16
    for (let i = 0; i < inputData.length; i++) {
      pcmData[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
    }

    sendAudioChunk(pcmData);
  };

  source.connect(processor);
  processor.connect(audioContext.destination);
}

// 启动录音
startRecording();
```

---

#### Python 示例代码

```python
import asyncio
import websockets
import json
import base64
import pyaudio

async def stream_audio():
    uri = "ws://106.55.166.12:8001/asr/stream"

    async with websockets.connect(uri) as websocket:
        # 1. 发送配置
        config = {
            "type": "config",
            "config": {
                "threshold": 0.6,
                "min_speech_duration_ms": 400,
                "min_silence_for_sentence_ms": 500,
                "min_silence_for_session_ms": 1500
            }
        }
        await websocket.send(json.dumps(config))

        # 2. 启动音频录制
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )

        # 3. 异步发送和接收
        async def send_audio():
            while True:
                audio_data = stream.read(4096)
                message = {
                    "type": "audio",
                    "data": base64.b64encode(audio_data).decode('utf-8')
                }
                await websocket.send(json.dumps(message))
                await asyncio.sleep(0.01)

        async def receive_results():
            while True:
                response = await websocket.recv()
                message = json.loads(response)

                if message['type'] == 'result':
                    print(f"转写结果: {message['text']}")
                    print(f"语言: {message['language']}")

                    if message['session_ended']:
                        print("会话结束")
                        break

                elif message['type'] == 'session_end':
                    print("会话结束（无音频）")
                    break

        # 并发执行发送和接收
        await asyncio.gather(send_audio(), receive_results())

# 运行
asyncio.run(stream_audio())
```

---

## 使用场景

### 场景1: 实时语音助手
用户持续对话，系统实时转写每句话：
```
用户: "今天天气怎么样" (0.5秒停顿)
系统: → 转写返回，继续监听
用户: "明天会下雨吗" (0.5秒停顿)
系统: → 转写返回，继续监听
用户: (1.5秒无声)
系统: → 会话结束，停止录音
```

### 场景2: 语音输入表单
用户一次性输入完整信息：
```
用户: "我的名字是张三，电话号码是1388888888" (1.5秒停顿)
系统: → 转写返回并自动结束
```

### 场景3: 会议记录
长时间录音，自动分句：
```
用户: "首先我们讨论第一个议题" (0.5秒)
系统: → 转写，继续
用户: "关于这个问题我有三点看法" (0.5秒)
系统: → 转写，继续
...持续对话...
```

---

## 常见问题

### Q1: 为什么有时候转写结果是空的？
A: 系统会过滤掉：
- 时长小于 400ms 的音频
- 纯噪音的音频段
- Whisper 返回的空白结果

### Q2: 如何调整灵敏度？
A: 通过 `config` 消息调整：
- 提高 `threshold` (如 0.7-0.8) → 降低灵敏度，减少噪音误触发
- 降低 `threshold` (如 0.4-0.5) → 提高灵敏度，捕捉更轻的声音

### Q3: 可以修改停顿时长吗？
A: 可以！通过 `config` 消息：
- `min_silence_for_sentence_ms`: 句子间停顿（推荐 300-1000ms）
- `min_silence_for_session_ms`: 会话结束停顿（推荐 1000-3000ms）

### Q4: 支持哪些音频格式？
A:
- **WebSocket 流式**: 只支持 PCM 16kHz mono int16
- **文件上传**: 支持 MP3, WAV, M4A, FLAC 等常见格式

### Q5: 如何判断用户是否说完了？
A: 监听 `result` 消息中的 `session_ended` 字段：
- `false`: 句子结束，继续监听
- `true`: 会话结束，应停止录音

---

## 测试工具

### 在线测试页面
```
http://106.55.166.12:8080/web/stream_asr_test.html
```

功能：
- 实时调整 VAD 参数
- 可视化状态显示
- 转写历史记录

### HTTP 端点测试
访问自动生成的 API 文档：
```
http://106.55.166.12:8001/docs
```

---

## 技术栈

- **ASR 引擎**: OpenAI Whisper (faster-whisper)
- **VAD**: Silero-VAD
- **Web 框架**: FastAPI
- **WebSocket**: Starlette
- **音频处理**: NumPy, PyAudio

---

## 更新日志

### v1.1.0 (2025-11-25)
- ✅ 新增智能两级停顿检测（句子/会话）
- ✅ 新增可配置 VAD 参数
- ✅ 新增空音频过滤机制
- ✅ 新增 `session_end` 消息类型
- ✅ 优化噪音敏感度
- ✅ 修复重复转写问题

### v1.0.0
- 初始版本
- 基础文件上传转写
- WebSocket 流式转写
- VAD 自动分句

---

## 联系支持

如有问题或建议，请联系开发团队。
