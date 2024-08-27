""""
    语音识别
"""
from abc import ABCMeta, abstractmethod

from robot import config, logging

logger = logging.getLogger(__name__)
class AbstractASR(object):
    """
    Generic parent class for all ASR engines
    """

    __metaclass__ = ABCMeta

    @classmethod
    def get_config(cls):
        return {}

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    @abstractmethod
    def transcribe(self, fp):
        pass

class FunASR(AbstractASR):
    """
    达摩院FunASR实时语音转写服务软件包
    """

    SLUG = "fun-asr"

    def __init__(self, inference_type, model_dir, **args):
        super(self.__class__, self).__init__()


    @classmethod
    def get_config(cls):
        return config.get("fun_asr", {})

    def transcribe(self, fp):
        print(fp)
        print("====================")
        return ""
        result = self.engine(fp)
        if result:
            logger.info(f"{self.SLUG} 语音识别到了：{result}")
            return result
        else:
            logger.critical(f"{self.SLUG} 语音识别出错了", stack_info=True)
            return ""

def get_engine_by_slug(slug=None):
    """
    Returns:
        An ASR Engine implementation available on the current platform

    Raises:
        ValueError if no speaker implementation is supported on this platform
    """
    print(slug)
    if not slug or type(slug) is not str:
        raise TypeError("无效的 ASR slug '%s'", slug)

    selected_engines = list(
        filter(
            lambda engine: hasattr(engine, "SLUG") and engine.SLUG == slug,
            get_engines(),
        )
    )

    if len(selected_engines) == 0:
        raise ValueError(f"错误：找不到名为 {slug} 的 ASR 引擎")
    else:
        if len(selected_engines) > 1:
            logger.warning(f"注意: 有多个 ASR 名称与指定的引擎名 {slug} 匹配")
        engine = selected_engines[0]
        logger.info(f"使用 {engine.SLUG} ASR 引擎")
        return engine.get_instance()


def get_engines():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        engine
        for engine in list(get_subclasses(AbstractASR))
        if hasattr(engine, "SLUG") and engine.SLUG
    ]