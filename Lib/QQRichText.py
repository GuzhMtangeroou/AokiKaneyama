# coding:utf-8
#   __  __       ____       _         ____        _   _____
#  |  \/  |_   _|  _ \ __ _(_)_ __   | __ )  ___ | |_|___  \
#  | |\/| | | | | |_) / _` | | '_ \  |  _ \ / _ \| __| __) |
#  | |  | | |_| |  _ < (_| | | | | | | |_) | (_) | |_ / __/
#  |_|  |_|\__,_|_| \_\__,_|_|_| |_| |____/ \___/ \__|_____|

"""
QQRichText
QQ富文本处理
"""

import re
import Lib.OnebotAPI as OnebotAPI


# CQ解码
def cq_decode(text, in_cq: bool = False) -> str:
    text = str(text)
    if in_cq:
        return text.replace("&amp;", "&").replace("&#91;", "["). \
            replace("&#93;", "]").replace("&#44;", ",")
    else:
        return text.replace("&amp;", "&").replace("&#91;", "["). \
            replace("&#93;", "]")


# CQ编码
def cq_encode(text, in_cq: bool = False) -> str:
    text = str(text)
    if in_cq:
        return text.replace("&", "&amp;").replace("[", "&#91;"). \
            replace("]", "&#93;").replace(",", "&#44;")
    else:
        return text.replace("&", "&amp;").replace("[", "&#91;"). \
            replace("]", "&#93;")


def cq_2_array(cq: str) -> list:
    if not isinstance(cq, str):
        raise TypeError("cq_2_array: 输入类型错误")

    # 匹配CQ码或纯文本（纯文本不含[]，利用这一点区分CQ码和纯文本）
    pattern = r"\[CQ:(\w+)(?:,([^\]]+))?\]|([^[\]]+)"

    # 匹配CQCode
    list_ = re.findall(pattern, cq)
    cq_array = []
    # 处理CQ码
    for rich in list_:
        # CQ码的结果类似('at', 'qq=114514', '')，而纯文本类似('', '', ' -  &#91;x&#93; 使用 `&amp;data` 获取地址')
        # 检测第一个值是否为空字符串即可区分

        if rich[0]:  # CQ码
            cq_array.append({
                "type": rich[0],  # CQ码类型
                "data": dict(
                    map(
                        lambda x: cq_decode(x, in_cq=True).split("="),
                        rich[1].split(",")
                    )
                ) if rich[1] else {},
            })
        else:  # 纯文本
            cq_array.append({
                "type": "text",
                "data": {
                    "text": cq_decode(rich[2])
                }
            })
    return cq_array


def array_2_cq(cq_array: list | dict) -> str:
    # 特判
    if isinstance(cq_array, dict):
        cq_array = [cq_array]

    if not isinstance(cq_array, (list, tuple)):
        raise TypeError("array_2_cq: 输入类型错误")

    # 将json形式的富文本转换为CQ码
    text = ""
    for segment in cq_array:
        # 纯文本
        if segment.get("type") == "text":
            text += cq_encode(segment.get("data").get("text"))
        # CQ码
        else:
            if segment.get("data"):  # 特判
                text += f"[CQ:{segment.get('type')}," + ",".join(
                    [cq_encode(x, in_cq=True) + "=" + cq_encode(segment.get("data")[x], in_cq=True)
                     for x in segment.get("data").keys()]) + "]"
            else:
                text += f"[CQ:{segment.get('type')}]"
    return text


class Segment:
    def __init__(self, cq):
        self.cq = cq
        if isinstance(cq, str):
            self.array = cq_2_array(cq)[0]
            self.type, self.data = list(self.array.values())
        elif isinstance(cq, dict):
            self.array = cq
            self.cq = array_2_cq(self.array)
            self.type, self.data = list(self.array.values())
        else:
            for segment in segments:
                if isinstance(cq, segment):
                    self.array = cq.array
                    self.cq = str(self.cq)
                    self.type, self.data = list(self.array.values())
                    break
            else:
                raise TypeError("Segment: 输入类型错误")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        self.cq = array_2_cq(self.array)
        return self.cq

    def __setitem__(self, key, value):
        self.array[key] = value

    def __getitem__(self, key):
        return self.array["data"].get(key)

    def __delitem__(self, key):
        del self.array["data"][key]

    def __eq__(self, other):
        other = Segment(other)
        return self.array == other.array

    def __contains__(self, other):
        if isinstance(other, Segment):
            return all(item in self.array for item in other.array)
        else:
            try:
                return str(other) in str(self)
            except (TypeError, AttributeError):
                return False


class Text(Segment):
    def __init__(self, text):
        super().__init__(text)
        self.text = self["text"] = text

    def __add__(self, other):
        other = Text(other)
        return self.text + other.text

    def __eq__(self, other):
        other = Text(other)
        return self.text == other.text

    def __contains__(self, other):
        if isinstance(other, Text):
            return other.text in self.text
        else:
            try:
                return str(other) in str(self.text)
            except (TypeError, AttributeError):
                return False

    def set_text(self, text):
        self.text = text
        self["text"] = text


class Face(Segment):
    def __init__(self, face_id):
        self.face_id = face_id
        super().__init__({"type": "face", "data": {"id": str(face_id)}})

    def set_id(self, face_id):
        self.face_id = face_id
        self.array["data"]["id"] = str(face_id)


class At(Segment):
    def __init__(self, qq):
        self.qq = qq
        super().__init__({"type": "at", "data": {"qq": str(qq)}})

    def set_id(self, qq_id):
        self.qq = qq_id
        self.array["data"]["qq"] = str(qq_id)


class Image(Segment):
    def __init__(self, file):
        self.file = file
        super().__init__({"type": "image", "data": {"file": str(file)}})

    def set_file(self, file):
        self.file = file
        self.array["data"]["file"] = str(file)


class Record(Segment):
    def __init__(self, file):
        self.file = file
        super().__init__({"type": "record", "data": {"file": str(file)}})

    def set_file(self, file):
        self.file = file
        self.array["data"]["file"] = str(file)


class Video(Segment):
    def __init__(self, file):
        self.file = file
        super().__init__({"type": "video", "data": {"file": str(file)}})

    def set_file(self, file):
        self.file = file
        self.array["data"]["file"] = str(file)


class Rps(Segment):
    def __init__(self):
        super().__init__({"type": "rps"})


class Dice(Segment):
    def __init__(self):
        super().__init__({"type": "dice"})


class Shake(Segment):
    def __init__(self):
        super().__init__({"type": "shake"})


# 戳一戳（未完全实现）
class Poke(Segment):
    def __init__(self, type_):
        self.type = type_
        super().__init__({"type": "poke", "data": {"type": str(self.type)}})

    def set_type(self, qq_type):
        self.type = qq_type
        self.array["data"]["type"] = str(qq_type)


class Anonymous(Segment):
    def __init__(self, ignore=False):
        self.ignore = 0 if ignore else 1
        super().__init__({"type": "anonymous", "data": {"ignore": str(self.ignore)}})

    def set_ignore(self, ignore):
        self.ignore = 0 if ignore else 1
        self.array["data"]["ignore"] = str(self.ignore)


class Share(Segment):
    def __init__(self, url, title, content="", image=""):
        self.url = url
        self.title = title
        self.content = content
        self.image = image
        super().__init__({"type": "share", "data": {"url": str(self.url), "title": str(self.title)}})

        if content != "":
            self.array["data"]["content"] = str(self.content)

        if image != "":
            self.array["data"]["image"] = str(self.image)

    def set_url(self, url):
        self.array["data"]["url"] = str(url)
        self.url = url

    def set_title(self, title):
        self.title = title
        self.array["data"]["title"] = str(title)

    def set_content(self, content):
        self.content = content
        self.array["data"]["content"] = str(content)

    def set_image(self, image):
        self.image = image
        self.array["data"]["image"] = str(image)


class Contact(Segment):
    def __init__(self, type_, id_):
        self.type = type_
        self.id = id_
        super().__init__({"type": "contact", "data": {"type": str(self.type), "id": str(self.id)}})

    def set_type(self, type_):
        self.type = type_
        self.array["data"]["type"] = str(type_)

    def set_id(self, id_):
        self.id = id_
        self.array["data"]["id"] = str(id_)


class Location(Segment):
    def __init__(self, lat, lon, title="", content=""):
        self.lat = lat
        self.lon = lon
        self.title = title
        self.content = content
        super().__init__({"type": "location", "data": {"lat": str(self.lat), "lon": str(self.lon)}})

        if title != "":
            self.array["data"]["title"] = str(self.title)

        if content != "":
            self.array["data"]["content"] = str(self.content)

    def set_lat(self, lat):
        self.lat = lat
        self.array["data"]["lat"] = str(lat)

    def set_lon(self, lon):
        self.lon = lon
        self.array["data"]["lon"] = str(lon)


class Music(Segment):
    def __init__(self, type_, id_):
        self.type = type_
        self.id = id_
        super().__init__({"type": "music", "data": {"type": str(self.type), "id": str(self.id)}})

    def set_type(self, type_):
        self.type = type_
        self.array["data"]["type"] = str(type_)

    def set_id(self, id_):
        self.id = id_
        self.array["data"]["id"] = str(id_)


class CustomizeMusic(Segment):
    def __init__(self, url, audio, image, title, content):
        self.url = url
        self.audio = audio
        self.image = image
        self.title = title
        self.content = content
        super().__init__({"type": "music", "data": {"type": "custom", "url": str(self.url), "audio": str(self.audio),
                                                    "image": str(self.image), "title": str(self.title),
                                                    "content": str(self.content)}})

    def set_url(self, url):
        self.url = url
        self.array["data"]["url"] = str(url)

    def set_audio(self, audio):
        self.audio = audio
        self.array["data"]["audio"] = str(audio)

    def set_image(self, image):
        self.image = image
        self.array["data"]["image"] = str(image)

    def set_title(self, title):
        self.title = title
        self.array["data"]["title"] = str(title)

    def set_content(self, content):
        self.content = content
        self.array["data"]["content"] = str(content)


class Reply(Segment):
    def __init__(self, message_id):
        self.message_id = message_id
        super().__init__({"type": "reply", "data": {"id": str(self.message_id)}})

    def set_message_id(self, message_id):
        self.message_id = message_id
        self.array["data"]["id"] = str(self.message_id)


class Forward(Segment):
    def __init__(self, forward_id):
        self.forward_id = forward_id
        super().__init__({"type": "forward", "data": {"id": str(self.forward_id)}})

    def set_forward_id(self, forward_id):
        self.forward_id = forward_id
        self.array["data"]["id"] = str(self.forward_id)


# 并不是很想写这个东西.png
# class CustomizeForward(Segment):
#     def __init__(self, title, content, source):
#         self.title = title
#         self.content = content
#         self.source = source
#         super().__init__({"type": "forward", "data": {"title": str(self.title)
#         , "content": str(self.content), "source": str(self.source)}})
#
#     def set_title(self, title):
#         self.array["data"]["title"] = str(self.title)
#         self.title = title
#
#     def set_content(self, content):


class XML(Segment):
    def __init__(self, xml):
        self.xml = xml
        super().__init__({"type": "xml", "data": {"xml": str(self.xml)}})

    def set_xml(self, xml):
        self.xml = xml
        self.array["data"]["xml"] = str(self.xml)


class JSON(Segment):
    def __init__(self, data):
        self.data = data
        super().__init__({"type": "json", "data": {"json": str(self.data)}})

    def set_json(self, data):
        self.data = data
        self.array["data"]["json"] = str(self.data)


segments = [Text, Face, Image, Record, At, Share, Music, CustomizeMusic, Reply, Forward, XML, JSON]


class QQRichText:

    def __init__(self, *rich):
        self.rich_array = rich

        # 特判
        if len(self.rich_array) == 1:
            self.rich_array = self.rich_array[0]

        # 识别输入的是CQCode or json形式的富文本
        # 如果输入的是CQCode，则转换为json形式的富文本

        # 处理CQCode
        if isinstance(self.rich_array, str):
            self.rich_string = self.rich_array
            self.rich_array = cq_2_array(self.rich_string)

        elif isinstance(self.rich_array, dict):
            self.rich_array = [self.rich_array]
        elif isinstance(self.rich_array, (list, tuple)):
            array = []
            for item in self.rich_array:
                if isinstance(item, dict):
                    array.append(item)
                elif isinstance(item, str):
                    array.append(cq_2_array(item)[0])
                else:
                    for segment in segments:
                        if isinstance(item, segment):
                            array.append(item.array)
                            break
                    else:
                        if isinstance(self.rich_array, QQRichText):
                            array += self.rich_array.rich_array
                        else:
                            raise TypeError("QQRichText: 输入类型错误")
            self.rich_array = array
        else:
            for segment in segments:
                if isinstance(self.rich_array, segment):
                    self.rich_array = [self.rich_array.array]
                    break
            else:
                if isinstance(self.rich_array, QQRichText):
                    self.rich_array = self.rich_array.rich_array
                else:
                    raise TypeError("QQRichText: 输入类型错误")

    def __str__(self):
        self.rich_string = array_2_cq(self.rich_array)
        return self.rich_string

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        return self.rich_array[index]

    def __add__(self, other):
        other = QQRichText(other)
        return self.rich_array + other.rich_array

    def __eq__(self, other):
        other = QQRichText(other)

        return self.rich_array == other.rich_array

    def __contains__(self, other):
        if isinstance(other, QQRichText):
            return all(item in self.rich_array for item in other.rich_array)
        else:
            try:
                return str(other) in str(self)
            except (TypeError, AttributeError):
                return False

    def send(self, user_id=None, group_id=None):
        OnebotAPI.OnebotAPI().send_msg(user_id=user_id, group_id=group_id, message=str(self))


# 单元测试
if __name__ == "__main__":
    # 测试CQ解码
    print(cq_decode(" - &#91;x&#93; 使用 `&amp;data` 获取地址"))

    # 测试CQ编码
    print(cq_encode(" - [x] 使用 `&data` 获取地址"))

    # 测试QQRichText
    rich = QQRichText(
        "[CQ:share,title=标题,url=https://baidu.com] [CQ:at,qq=1919810] -  &#91;x&#93; 使用 `&amp;data` 获取地址")
    print(rich.rich_array)
    print(rich)

    print(QQRichText(At(114514)))
    print(Segment(At(1919810)))
    print(QQRichText({"type": "at", "data": {"qq": "1919810"}}))
