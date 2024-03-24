# coding:utf-8
#   __  __       ____       _         ____        _   _____
#  |  \/  |_   _|  _ \ __ _(_)_ __   | __ )  ___ | |_|___  \
#  | |\/| | | | | |_) / _` | | '_ \  |  _ \ / _ \| __| __) |
#  | |  | | |_| |  _ < (_| | | | | | | |_) | (_) | |_ / __/
#  |_|  |_|\__,_|_| \_\__,_|_|_| |_| |____/ \___/ \__|_____|

from Lib.MuRainLib import *
import Lib.XiaosuEventManager
import Lib.OnebotAPI
import Lib.QQRichText

import Lib.ConfigManager as ConfigManager
import Lib.EventManager as EventManager
import Lib.PluginManager as PluginManager
import Lib.LoggerManager as LoggerManager
import Lib.BotController as BotController
import Lib.MessageManager as MessageManager
import Lib.Configs as Configs
import Lib.Events as Events


VERSION = "2.0.0-dev"
VERSION_WEEK = "24W13A"


# Lib信息
class LibInfo:
    def __init__(self):
        self.version = VERSION
        self.version_week = VERSION_WEEK

    def get_version(self):
        return self.version, self.version_week
