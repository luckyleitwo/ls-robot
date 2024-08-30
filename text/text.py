from robot.ASR import asr_text
from robot.Conversation import Conversation

# asr_text('/Users/shenglei/ls/ls-robot/MP4到MP3转换器- FreeConvert.com.mp3')

conversationz = Conversation(False)

conversationz.doResponse(query="讲一个200字的笑话")
