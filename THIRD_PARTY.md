# 资源来源与许可

本版保留 LinguaMiner 原始 MIT 许可与版权声明。模型和词典由安装程序从各自来源下载，不打包进入源码仓库。

| 资源 | 来源 | 许可及说明 |
|---|---|---|
| LinguaMiner | https://github.com/thecopybookhare-cmd/lingua-miner | MIT，见根目录 LICENSE |
| ECDICT | https://github.com/skywind3000/ECDICT | MIT；使用 1.0.28 StarDict 英汉版，由原有词典导入器安装 |
| 英汉句子翻译 | https://huggingface.co/Helsinki-NLP/opus-mt-en-zh | 模型卡标注 Apache-2.0；下载 OPUS 2020-07-17 原模型，使用 CTranslate2 转换；目标标记 cmn_Hans |
| Whisper small | https://huggingface.co/Systran/faster-whisper-small | 原 Whisper 模型 MIT；由 faster-whisper 加载 |
| 英语语言模型 | https://huggingface.co/spacy/en_core_web_sm | MIT，模型及依赖使用各自许可 |
| 英语发音 | https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/amy/low | 使用原项目配置的 Piper 语音；具体语音与数据集许可见该目录 MODEL_CARD |
| FFmpeg | https://ffmpeg.org/legal.html | 构建选项决定 LGPL/GPL 适用范围；由原项目 static-ffmpeg 获取，不在源码包附带二进制 |

ECDICT 下载文件 `ecdict-stardict-28.zip` 的 SHA-256：
`c707d0f3ded6ec79b96466da4a1574e074703da5af9c120fbad97f9cb08c6f2c`。

其他 Python 依赖保持原项目选择，清单位于 pyproject.toml / uv.lock；其许可不因本仓库使用 MIT 而改变。
本仓库不提供电影、电视剧或配套影视字幕下载；测试用个人视频不会发布。
