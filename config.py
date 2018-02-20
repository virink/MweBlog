#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import time
import os


__AUTHER__ = "Virink <virink@outlook.com>"
__BLOG__ = "https://www.virzz.com"
__GITHUB__ = "https://github.com/virink"

__NAME__ = "mweblog"
__VERSION__ = "0.1"
DESCRIPTION = "A plugin for MWeb to generate website"

BLOG_ROOT = "/Users/virink/Workspace/Blog"

# Document
DOC_ROOT = "/Users/virink/Documents/MyDocs"
DOCS = {
    "db": DOC_ROOT + "/mainlib.db",
    "doc": DOC_ROOT + "/docs/",
    "meta": DOC_ROOT + "/metadata/",
    "blog_cat": ["Blog", "test"]
}

# docs
# metadata

# Site
TITLE = "Virink's Blog"
SUBTITLE = "Let life be beautiful like summer flowers, and death like autume leaves."
DESCRIPTION = "Virink的小站,记录杂文与分享一些技术文章"
KEYWORDS = "PHP,CODE,AUDIT,CTF,Writeup,Sec,Virink,代码审计,技术博客"
AUTHOR = "Virink"
EMAIL = "virink@outlook.com"
LANGUAGE = "zh-CN"
TIMEZONE = "Asia/Shanghai"

# URL
URL = 'https://www.virzz.com'
COS = "img.virzz.com"
ROOT = "/"
# strftime and string format
PERMALINK = "/%Y/%m/%d/{title}.html"

# Directory
PUBLIC_DIR = "public"
ARCHIVES_DIR = "archives"
TAGS_DIR = "tags"
PUBLIC_PATH = os.path.join(BLOG_ROOT, PUBLIC_DIR)

# Date / Time format
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SITEMAP_FORMAT = "%Y-%m-%dT%H:%M:%S+08:00"

# Pagination
PAGINATION = {
    "per": 10,
    "dir": "page"
}

# Themes
THEME = "default"

# Sitemap
SITEMAP = {
    "path": "sitemap",
    "template": "sitemap"
}

# Feed
FEED = {
    "num": 50,
    "path": ["feed", "atom"],
    "template": "feed"
}

# Social
SOCIAL = {
    "github": "virink",
    "twitter": "virinkz",
    "telegram": "virink"
}

AUTHFILE = [
    'google02996eb2dd5b9b34.html', 'qcloud_cdn.html'
]

# Deployment
DEPLOY = {
    "type": "git",
    # "repository": "git@github.com:virink/virink.github.io.git",
    "repository": "git@github.com:virink/testblog.git",
    "branch": "master",
    "message": "Updated %s By %s %s" % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), __NAME__, __VERSION__)
}

if __name__ == '__main__':
    print("Error")
