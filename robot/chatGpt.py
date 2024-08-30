# -*- coding: utf-8 -*-
import os
import json
import random
import requests
import openai

from uuid import getnode as get_mac
from abc import ABCMeta, abstractmethod
from robot import logging, config, utils

logger = logging.getLogger(__name__)


class AbstractRobot(object):
    __metaclass__ = ABCMeta

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chat(self, texts, parsed):
        pass

    @abstractmethod
    def stream_chat(self, texts):
        pass


class OPENAIRobot(AbstractRobot):
    SLUG = "openai"

    def __init__(
            self,
            openai_api_key,
            model,
            provider,
            api_version,
            temperature,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            stop_ai,
            prefix="",
            proxy="",
            api_base="",
    ):
        """
        OpenAI机器人
        """
        super(self.__class__, self).__init__()
        self.openai = None
        try:
            import openai

            self.openai = openai
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            self.openai.api_key = openai_api_key
            if proxy:
                logger.info(f"{self.SLUG} 使用代理：{proxy}")
                self.openai.proxy = proxy
            else:
                self.openai.proxy = None

        except Exception:
            logger.critical("OpenAI 初始化失败，请升级 Python 版本至 > 3.6")
        self.model = model
        self.prefix = prefix
        self.provider = provider
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop_ai = stop_ai
        self.api_base = api_base if api_base else "https://api.openai.com/v1/chat"
        self.context = []

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("openai", {})

    def stream_chat(self, texts,stream=True):
        """
        从ChatGPT API获取回复
        :return: 回复
        """

        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        self.context.append({"role": "user", "content": msg})

        header = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer " + self.openai.api_key
        }
        if self.provider == 'openai':
            header['Authorization'] = "Bearer " + self.openai.api_key
        elif self.provider == 'azure':
            header['api-key'] = self.openai.api_key
        else:
            raise ValueError("Please check your config file, OpenAiRobot's provider should be openai or azure.")

        logger.info(f"使用模型：{self.model}，开始流式请求")
        url = self.api_base + "/completions"
        logger.info(url)
        # 请求接收流式数据
        try:

            # optional; defaults to `os.environ['OPENAI_API_KEY']`
            # openai.api_key = "sk-hSaUp2XwPvZB4zdVShdYiFVC0Exc2dwOOpoKaYaemeLAbGCW"

            # all client options can be configured just like the `OpenAI` instantiation counterpart
            # openai.base_url = "https://api.chatanywhere.tech/v1/"
            openai.api_key = 'sk-ZRD4wE1uJUhTm0xh7d5152D55f994b78961540665a50Ff00'
            openai.base_url = "https://free.gpt.ge/v1/"
            openai.default_headers = {"x-foo": "true"}
            logger.info(self.context)
            response = openai.chat.completions.create(
                model=self.model,
                messages=self.context,
                stream=stream
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response:
                    if line.choices:
                        if len(line.choices) > 0:
                            choice = line.choices[0]
                            if choice.delta:
                                delta = choice.delta
                                if delta.role:
                                    role = delta.role
                                elif delta.content:
                                    delta_content = delta.content
                                    i += 1
                                    if i < 40:
                                        logger.debug(delta_content, end="")
                                    elif i == 40:
                                        logger.debug("......")
                                    one_message["content"] = (
                                            one_message["content"] + delta_content
                                    )
                                    yield delta_content

        except Exception as e:
            ee = e

            def generate():
                yield "request error:\n" + str(ee)

        return generate if stream else response.choices[0].message.content

    def chat(self, texts, parsed):
        """
        使用OpenAI机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        try:
            # optional; defaults to `os.environ['OPENAI_API_KEY']`
            openai.api_key = "sk-hSaUp2XwPvZB4zdVShdYiFVC0Exc2dwOOpoKaYaemeLAbGCW"
            self.context.append({"role": "user", "content": msg})
            # all client options can be configured just like the `OpenAI` instantiation counterpart
            openai.base_url = "https://free.gpt.ge/v1/"
            openai.default_headers = {"x-foo": "true"}
            response = openai.chat.completions.create(
                model=self.model,
                messages=self.context,
                # stream=True
            )
            logger.info("进去openai响应")
            return response.choices[0].message.content
        except self.openai.error.InvalidRequestError:
            logger.warning("token超出长度限制，丢弃历史会话")
            self.context = []
            return self.chat(texts, parsed)
        except Exception:
            logger.critical(
                "openai robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉，OpenAI 回答失败"


def get_unknown_response():
    """
    不知道怎么回答的情况下的答复

    :returns: 表示不知道的答复
    """
    results = ["抱歉，我不会这个呢", "我不会这个呢", "我还不会这个呢", "我还没学会这个呢", "对不起，你说的这个，我还不会"]
    return random.choice(results)


def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = list(
        filter(
            lambda robot: hasattr(robot, "SLUG") and robot.SLUG == slug, get_robots()
        )
    )
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            logger.warning(
                "WARNING: Multiple robots found for slug '%s'. "
                + "This is most certainly a bug." % slug
            )
        robot = selected_robots[0]
        logger.info(f"使用 {robot.SLUG} 对话机器人")
        return robot.get_instance()


def get_robots():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        robot
        for robot in list(get_subclasses(AbstractRobot))
        if hasattr(robot, "SLUG") and robot.SLUG
    ]
