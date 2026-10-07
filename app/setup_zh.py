"""Prepare Chinese-edition resources using LinguaMiner's existing engines."""
import hashlib
import re
import shutil
import tempfile
import threading
import zipfile
from pathlib import Path

import requests

from . import config, userdict

ECDICT_URL = (
    "https://github.com/skywind3000/ECDICT/releases/download/1.0.28/"
    "ecdict-stardict-28.zip"
)
ECDICT_SHA256 = "c707d0f3ded6ec79b96466da4a1574e074703da5af9c120fbad97f9cb08c6f2c"
ECDICT_SLUG = "ecdict-english-chinese"
_LOCK = threading.Lock()


def dictionary_ready() -> bool:
    return any(d["slug"] == ECDICT_SLUG and d["entries"] > 0
               for d in userdict.list_dicts())


def _sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def ensure_dictionary(archive: Path | None = None) -> dict:
    """Download the pinned release and import it through the existing importer."""
    with _LOCK:
        if dictionary_ready():
            return next(d for d in userdict.list_dicts() if d["slug"] == ECDICT_SLUG)
        archive = archive or config.DL_DIR / "ecdict-stardict-28.zip"
        if not archive.exists():
            part = archive.with_suffix(".part")
            try:
                with requests.get(ECDICT_URL, stream=True, timeout=(30, 120)) as response:
                    response.raise_for_status()
                    with part.open("wb") as output:
                        for chunk in response.iter_content(1 << 20):
                            output.write(chunk)
                if _sha256(part) != ECDICT_SHA256:
                    raise ValueError("英汉词典下载校验失败，请重新安装资源。")
                part.replace(archive)
            finally:
                part.unlink(missing_ok=True)
        if _sha256(archive) != ECDICT_SHA256:
            raise ValueError("英汉词典文件校验失败，请删除损坏的下载文件后重试。")
        with tempfile.TemporaryDirectory(dir=config.TEMP_DIR) as temp:
            folder = Path(temp)
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.infolist():
                    name = Path(member.filename).name
                    if member.is_dir() or not name.endswith((".ifo", ".idx", ".dict", ".dict.dz")):
                        continue
                    # Only dictionary components, flattened into our temporary folder.
                    target = folder / name
                    if target.exists():
                        raise ValueError("词典压缩包包含重复文件。")
                    with bundle.open(member) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
            ifos = list(folder.glob("*.ifo"))
            if len(ifos) != 1:
                raise ValueError("词典压缩包缺少唯一的 StarDict 描述文件。")
            info = ifos[0].read_text(encoding="utf-8")
            # Reserve a stable slug; do not overwrite a user's generic 'dic' dictionary.
            info = re.sub(r"(?m)^bookname=.*$", "bookname=ECDICT English-Chinese", info)
            ifos[0].write_text(info, encoding="utf-8")
            result = userdict.import_file(str(ifos[0]))
            if not result["entries"] or result["slug"] != ECDICT_SLUG:
                raise ValueError("英汉词典导入未完成。")
            return result


def prepare() -> None:
    from . import media, piper_tts, transcribe, translate

    print("正在安装英汉词典……", flush=True)
    print(ensure_dictionary(), flush=True)
    print("正在准备英汉句子翻译模型……", flush=True)
    if not translate.is_downloaded():
        translate.download()
    translated = translate.translate("I am learning English.")
    if not re.search(r"[\u3400-\u9fff]", translated):
        raise RuntimeError("英汉翻译验证失败，请检查下载日志后重试。")
    print("正在准备 Whisper small 英语字幕识别模型……", flush=True)
    transcribe._model("small")
    print("正在准备英语发音与视频组件……", flush=True)
    if not piper_tts.is_downloaded():
        piper_tts.download()
    if not media.ffmpeg_available():
        raise RuntimeError("FFmpeg 下载失败，请检查网络后重试。")
    print("离线资源准备完成。", flush=True)


if __name__ == "__main__":
    prepare()
