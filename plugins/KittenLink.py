from Lib import *
import time

api = OnebotAPI.OnebotAPI()
Linker_Userid="12177317"

#插件信息
class PluginInfo(PluginManager.PluginInfo):
    def __init__(self):
        super().__init__()
        self.NAME = "KittenLink"  # 插件名称
        self.AUTHOR = "vika"  # 插件作者
        self.VERSION = "1.0.0"  # 插件版本
        self.DESCRIPTION = "链接Kitten作品"  # 插件描述

def BEATING(codemaoid):
    if str(codemaoid) in Linker_Userid:
        return 1
    else:
        return -2
    
def SEND_GROUP_MSG(groupid,text,codemaoid):
    if str(codemaoid) == Linker_Userid:
        BotController.send_message(QQRichText.QQRichText(f'{text}'),group_id=groupid)
        return 1
    else:
        return -2
    
def SEND_PRIVATE_MSG(userid,text,codemaoid):
    if str(codemaoid) == Linker_Userid:
        BotController.send_message(QQRichText.QQRichText(f'{text}'),user_id=userid)
        return 1
    else:
        return -2
    
def main(command,codemaoid):
    if command == "BEATING":
        if BEATING(codemaoid) == 1:
            return "[Linker@beating]beat successfuly"
        elif BEATING(codemaoid) == -2:
            return "[Linker@beating]beat unsuccessfuly:userid error"
        else:
            return "[Linker@beating]beat unsuccessfuly"
    elif "SEND_GROUP_MSG" in command:
            groupid=str(command).split("&")[-2]
            text=str(command).split("&")[-1]
            if SEND_GROUP_MSG(groupid,text,codemaoid) == 1:
                return "[Linker@sendgroupmessage.message]done."
            elif SEND_GROUP_MSG(groupid,text,codemaoid) == -2:
                return "[Linker@sendgroupmessage.message]userid error."
    elif "SEND_PRIVATE_MSG" in command:
            groupid=str(command).split("&")[-2]
            text=str(command).split("&")[-1]
            if SEND_PRIVATE_MSG(groupid,text,codemaoid) == 1:
                return "[Linker@sendmessage.message]done."
            elif SEND_PRIVATE_MSG(groupid,text,codemaoid) == -2:
                return "[Linker@sendmessage.message]userid error."
    else:
            return "[Linker]unknown command"