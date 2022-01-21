from Products.FCKeditor.config import RUID_URL_PATTERN

import re


IMG = '<img title="broken image" alt="broken image" src="" />'


def removeInlineURI(text):
    pattern = re.compile(r"<img[^>]*src=[\'\"]data:[^>]*/>")
    text, count = pattern.subn(IMG, text)
    return text


def convert(self, orig, data, **kwargs):
    text = orig
    # XXX PATCH START XXX
    text = removeInlineURI(text)
    # XXX PATCH END XXX
    tags_ruid, unique_ruid = self.find_ruid(text)
    if unique_ruid:
        ruid_url = self.mapRUID_URL(unique_ruid, kwargs["context"])
        for tag_ruid in tags_ruid:
            t, uid = tag_ruid.items()[0]
            if uid in ruid_url:
                text = text.replace(
                    t,
                    t.lower().replace(
                        "./%s/%s" % (RUID_URL_PATTERN, uid), ruid_url[uid]
                    ),
                )

    data.setData(text)
    return data
