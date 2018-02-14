#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

__AUTHER__ = "Virink <virink@outlook.com>"
__BLOG__ = "https://www.virzz.com"
__GITHUB__ = "https://github.com/virink"

__NAME__ = "mweblog"
__VERSION__ = "0.1"
DESCRIPTION = "A plugin for MWeb to generate website"

import os
import sys
import time
import sqlite3
import re

from collections import defaultdict
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from biplist import *
from misaka import Markdown, HtmlRenderer, escape_html
from jinja2 import Environment, PackageLoader

from config import *
from links import LINKS

os.chdir(BLOG_ROOT)


class showInfo:

    cs = {
        'd': (30, 40),  # dark = black
        'r': (31, 41),
        'g': (32, 42),
        'y': (33, 43),
        'b': (34, 44),
        'p': (35, 45),
        'c': (36, 46),  # cyan
        'w': (37, 47)
    }
    t = True
    c = 'w'
    b = 'd'

    def _print(self, *msg):
        if self.t:
            print("\033[32;40m[%s]  " % (time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime())), end='')
        print("\033[%s;%sm" % (self.cs[self.c][0], self.cs[self.b][1]), end='')
        print(*msg, end='')
        print("\033[m")

    def print(self, *msg):
        self.c = 'w'
        self._print(*msg)

    def info(self, *msg):
        self.c = 'y'
        self._print(*msg)

    def warn(self, *msg):
        self.c = 'p'
        self._print(*msg)

    def error(self, *msg):
        self.c = 'r'
        self._print(*msg)

    def debug(self, *msg):
        self.c = 'c'
        self._print(*msg)

    def show(self, *msg, c='w', b='d'):
        self.c = c
        self.b = b
        self.t = False
        self._print(*msg)
        self.t = True
        self.b = 'd'

SI = showInfo()


class Generate:

    conn = None
    cursor = None
    tags = None
    tag_articles = None
    article_tags = None
    articles = None
    permalinks = {}
    sitemaps = {
        "article": [],
        "index": [],
        "tags": []
    }
    feeds = []
    md = None
    article_num = 0
    jinja2 = 0

    # Common Function

    def select(self, sql):
        if not self.cursor:
            self.conn = sqlite3.connect(DOCS['db'])
            self.cursor = self.conn.cursor()
        if not sql:
            return False
        results = self.cursor.execute(sql)
        return results.fetchall()

    def read_md_file(self, filename):
        filename = os.path.join(DOCS['doc'], "%s.md" % filename)
        if not os.path.exists(filename):
            return False
        with open(filename, 'r') as f:
            res = f.read()
            return res

    def write_html_file(self, filename, data, _type=".html"):
        with open(filename + _type, 'w') as f:
            f.write(data)

    def read_plist(self, filename):
        _img = False
        try:
            plist = readPlist(filename)
            _img = {}
            _plist = plist[plist['selectedItem']]
            if not _plist:
                return False
            for local, remote in plist[plist['selectedItem']][0].items():
                if COS in remote:
                    _img.update({local: remote})
        except (InvalidPlistException, NotBinaryPlistException) as e:
            print("Not a plist:", e)
            _img = False
        return _img

    # Method

    def get_tags(self):
        if self.tags:
            return self.tags
        sql = "select * from tag"
        res = self.select(sql)
        self.tags = dict(res)

    def get_article_upload_img(self):
        paths = os.listdir(DOCS['meta'])
        article_upload_img = {}
        for path in paths:
            if path.startswith("ImgUpload"):
                tmp = self.read_plist(os.path.join(DOCS['meta'], path))
                if tmp:
                    article_upload_img.update(tmp)
        return article_upload_img

    def get_tag_articles(self):
        if self.tag_articles and self.article_tags:
            return True
        sql = "select rid,aid from tag_article"
        res = self.select(sql)
        if not self.tags:
            self.get_tags()
        self.tag_articles = defaultdict(list)
        self.article_tags = defaultdict(list)
        for r in res:
            aid = r[1]
            tag = self.tags[r[0]]
            # article->tags
            self.article_tags[aid].append(tag)
            # tag->articles
            self.tag_articles[tag].append(aid)

    def get_blog_articles(self):
        where_sql = " or ".join(
            ["c.name = '%s'" % i for i in DOCS['blog_cat']])
        sql = "select a.uuid,a.docName,a.dateAdd,a.dateModif,a.dateArt from article a \
            LEFT JOIN cat_article ca on a.uuid=ca.aid \
            LEFT JOIN cat c on ca.rid=c.uuid \
            WHERE %s ORDER BY dateAdd DESC" % where_sql
        self.articles = self.select(sql)

    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def __init__(self):
        # tags
        self.get_tags()
        self.get_tag_articles()
        # articles
        self.get_blog_articles()
        # generate Markdown
        self.md = Markdown(
            HtmlRenderer(flags=('hard-wrap', 'skip-html')),
            extensions=('fenced-code',))
        # jinja2
        self.jinja2 = Environment(
            loader=PackageLoader('mweblog', "themes/%s" % THEME))
        # jinja2 globals
        self.jinja2.globals['title'] = TITLE
        self.jinja2.globals['subtitle'] = SUBTITLE
        self.jinja2.globals['description'] = DESCRIPTION
        self.jinja2.globals['url'] = URL
        self.jinja2.globals['author'] = AUTHOR
        self.jinja2.globals['language'] = LANGUAGE
        self.jinja2.globals['name'] = __NAME__
        self.jinja2.globals['pagi'] = PAGINATION
        self.jinja2.globals['tags_dir'] = TAGS_DIR
        # clear public
        os.system("rm -rf %s && mkdir %s" % (PUBLIC_PATH, PUBLIC_PATH))
        # sys.exit(1)
        # generate articles
        self.generate_articles()
        # generate tags
        self.generate_tags()
        # generate index
        self.generate_index()
        # generate achives
        # self.generate_achives()
        # generate about
        # self.generate_about()
        # generate links
        # self.generate_links()
        # generate sitemap
        self.generate_sitemap()
        # generate feed
        self.generate_feed()

    def generate_articles(self):
        SI.info("generate articles ...")
        if len(self.articles) < 1:
            print("Not Found articles")
            return False

        def generate_permalink(dateAdd, title):
            return time.strftime(PERMALINK.format(title=title), time.localtime(dateAdd))

        template = self.jinja2.get_template('article.html')
        # uuid, docName, dateAdd, dateModif, dateArt
        # title, slug, tags, dateAdd, dateModif, content
        n = 0
        for article in self.articles:
            n = n + 1
            uuid = article[0]
            SI.info("%s [%s]" % (n, uuid))
            _content = self.read_md_file(uuid)
            # get_article_upload_img
            article_upload_img = self.get_article_upload_img()
            for local, remote in article_upload_img.items():
                # if local in _content:
                _content = _content.replace(local, remote)
            # summary
            summary = re.findall(r'###?#? .*', _content)
            _content = _content.split("\n")
            title = _content[0][2:]
            content = self.md('\n'.join(_content[1:]))
            # tags
            if uuid in self.article_tags:
                tags = self.article_tags[uuid]
            else:
                SI.warn("[%s] (%s) no tags" % (uuid, title))
                tags = ""
            # date
            date = {
                "add": time.strftime(DATE_TIME_FORMAT, time.localtime(article[2])),
                "mod": time.strftime(DATE_TIME_FORMAT, time.localtime(article[3]))
            }
            if article[1]:
                slug = article[1]
            else:
                slug = False
            # permalink
            permalink = generate_permalink(article[2], slug or title)
            # print
            SI.print("%s %s\n\t\t\t-> %s" %
                     (date['mod'], title, permalink))
            # permalinks sitemaps feeds
            self.permalinks.update({uuid: permalink})
            self.sitemaps['article'].append({
                "loc": "%s%s" % (URL, permalink),
                "lastmod": time.strftime(SITEMAP_FORMAT, time.localtime(article[3]))
            })
            self.feeds.append({
                "uuid": uuid,
                "title": title,
                "url": permalink,
                "updated": date['mod'],
                "pushed": date['add'],
                # "content": content[:200] + '...',
                "summary": escape_html('\n'.join(summary)),
                "tags": tags,
            })
            # render html
            res = template.render(
                title=title, content=content, date=date, tags=tags)
            # write file
            filename = os.path.join(PUBLIC_PATH, permalink[1:])
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            if slug:
                self.write_html_file(filename, res)
            self.write_html_file(os.path.join(dirname, title), res)
        SI.info("generate articles (Total : %s) ok" % n)

    def generate_sitemap(self):
        SI.info("generate sitemap ...")
        template = self.jinja2.get_template('sitemap.xml')
        _sitemaps = self.sitemaps['article'][:100] \
            + self.sitemaps['tags'][:100] \
            + self.sitemaps['index'][:100]
        res = template.render(urls=_sitemaps)
        self.write_html_file(os.path.join(PUBLIC_PATH, "sitemap"), res, ".xml")
        SI.info("generate sitemap ok")

    def generate_feed(self):
        _feeds = sorted(self.feeds, key=lambda feed: feed[
                        "updated"], reverse=True)
        SI.info("generate feed ...")
        template = self.jinja2.get_template('feed.xml')
        _updated = time.strftime(SITEMAP_FORMAT, time.localtime())
        # entries
        res = template.render(updated=_updated, entries=_feeds[:FEED['num']])
        for p in FEED['path']:
            self.write_html_file(os.path.join(PUBLIC_PATH, p), res, ".xml")
            SI.print("-> %s.xml" % p)
        SI.info("generate feed ok")

    def generate_pagination(self, curr_page, total_page):
        return {
            "page": curr_page,
            "pre_page": [p for p in range(1, curr_page)],
            "next_page": [p for p in range(curr_page + 1, total_page + 1)]
        }

    def generate_index(self):
        SI.info("generate index ...")
        template = self.jinja2.get_template('index.html')
        per = PAGINATION['per']
        total_page = len(self.feeds) // per + 1
        # SI.debug(len(self.feeds))
        # SI.debug(total_page)
        # first page
        curr_page = 1
        pagination = self.generate_pagination(curr_page, total_page)
        res = template.render(
            pagination=pagination,
            articles=self.feeds[:curr_page * per])
        self.write_html_file(os.path.join(PUBLIC_PATH, "index"), res, ".html")
        SI.print("-> /index.html")
        # other page
        dirname = os.path.join(PUBLIC_PATH, "page")
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        for page in range(2, total_page + 1):
            pagination = self.generate_pagination(page, total_page)
            res = template.render(
                pagination=pagination,
                articles=self.feeds[(page - 1) * per:page * per])
            page = str(page)
            _fpd = os.path.join(PUBLIC_PATH, "page", page)
            if not os.path.exists(_fpd):
                os.makedirs(_fpd)
            self.write_html_file(os.path.join(dirname, page), res, ".html")
            SI.print("-> /page/%s.html" % page)
            self.write_html_file(os.path.join(_fpd, "index"), res, ".html")
            SI.print("-> /page/%s/index.html" % page)
        SI.info("generate index ok")

    def generate_tags(self):
        SI.info("generate tags ...")
        template = self.jinja2.get_template('tags.html')
        per = PAGINATION['per']
        _feeds_uuid = {feed['uuid']: feed for feed in self.feeds}
        SI.debug(_feeds_uuid.keys())
        for tag, articles in self.tag_articles.items():
            SI.info("generate tag [%s] ..." % tag)
            SI.print(tag, articles)
            total_page = len(articles) // per + 1
            # articles(uuid) to feeds
            _feeds = [_feeds_uuid[article]
                      for article in articles if article in _feeds_uuid]
            # first page
            curr_page = 1
            pagination = self.generate_pagination(curr_page, total_page)
            res = template.render(
                pagination=pagination, tag=tag,
                articles=_feeds[:curr_page * per])
            dirname = os.path.dirname(os.path.join(
                PUBLIC_PATH, TAGS_DIR, tag, "index"))
            SI.debug(dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            self.write_html_file(os.path.join(dirname, "index"), res, ".html")
            SI.print("-> /%s/%s/index.html" % (TAGS_DIR, tag))
            # other page
            dirname = os.path.join(dirname, "page")
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            for page in range(2, total_page + 1):
                pagination = self.generate_pagination(page, total_page)
                res = template.render(
                    pagination=pagination, tag=tag,
                    articles=_feeds[(page - 1) * per:page * per])
                page = str(page)
                _fpd = os.path.join(PUBLIC_PATH, TAGS_DIR, tag, "page", page)
                if not os.path.exists(_fpd):
                    os.makedirs(_fpd)
                self.write_html_file(os.path.join(dirname, page), res, ".html")
                SI.print("-> /%s/%s/page/%s.html" % (TAGS_DIR, tag, page))
                self.write_html_file(os.path.join(
                    dirname, page, "index"), res, ".html")
                SI.print("-> /%s/%s/page/%s/index.html" %
                         (TAGS_DIR, tag, page))
        SI.info("generate tags ok")
        # sys.exit(0)


def generate():
    SI.info("generate start...")
    _generate = Generate()
    SI.info("generate all ok...")


def deploy():
    print("deploy")
    DEPLOY_DIR = os.path.abspath(".deploy_git")
    if not os.path.exists(DEPLOY_DIR):
        print("setup")
        # setup
        os.mkdir(DEPLOY_DIR)
        os.chdir(os.path.join(BLOG_ROOT, DEPLOY_DIR))
        os.system("touch placeholder")
        git("init")
        git("add -A")
        git("commit -m First commit")
        git("remote add origin %s" % DEPLOY['repository'])
        git("push -u origin master")
    # setup .deploy_git
    # init, config user.name, config user.email, add -A, commit -m First commit
    else:
        print("push")
        # Clear .deploy_git
        clear_deploy_git()
        os.chdir(os.path.join(BLOG_ROOT, DEPLOY_DIR))
        # Copy public to .deploy_git
        os.system("cp -r ./public/ ./")
        git("add -A")
        git("commit -m \"%s\"" % DEPLOY['message'])
        git("push -u %s HEAD:%s --force" %
            (DEPLOY['repository'], DEPLOY['branch']))
    # push
    # add -A, commit -m xxx, push -u repo.url HEAD:repo.branch --force


def server():
    import random
    SI.print("server")
    if not os.path.exists(PUBLIC_PATH):
        os.makedirs(PUBLIC_PATH)
    PORT = 8088 + random.randint(1, 20)
    os.chdir(PUBLIC_PATH)
    with TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        SI.print("serving at port : ", PORT)
        SI.print("http://localhost:%s or http://127.0.0.1:%s" % (PORT, PORT))
        httpd.serve_forever()


def version():
    SI.show("Version : %s %s" % (__NAME__, __VERSION__))
    sys.exit(0)


def help():
    _help = """\n
    %s [action]\n
    action :\n
    deploy(d)\t\tPush to Github Pages
    generate(g)\t\tgenerate static html website
    server(s)\t\tRun a simple http server
    gd\t\t\tgenerate and deploy
    gs\t\t\tgenerate and server
    help(h)\t\t\tShow this message and exit
    version(v)\t\tShow version and exit
    """ % (__NAME__)
    SI.show(_help, c='d', b='w')
    sys.exit(0)


def git(argv):
    SI.show("emd : git %s" % argv)
    os.system("git %s" % argv)


def clear_deploy_git(path=os.path.abspath(".deploy_git")):
    path = path.replace('\\', '/')
    if not os.path.exists(path):
        return 0
    bname = os.path.basename(path)
    if os.path.isdir(path):
        if bname.startswith(".") and bname != ".deploy_git":
            return 0
        for p in os.listdir(path):
            clear_deploy_git(os.path.join(path, p))
        if bname != ".deploy_git":
            os.rmdir(path)
    else:
        os.remove(path)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        help()
    args = (sys.argv[1]).lower()
    start_time = time.time()
    if args == 't':
        t = 1
        print(t)
        sys.exit(1)
    if args == 'version' or args == "v":
        version()
    elif args == 'help' or args == "h":
        help()
    elif args == 'deploy' or args == "d":
        deploy()
    elif args == 'generate' or args == "g":
        generate()
    elif args == 'server' or args == "s":
        server()
    elif args == 'gd':
        generate()
        deploy()
    elif args == 'gs':
        generate()
        server()
    print()
    SI.debug("Total Usage Time : %4.4f sec" % (time.time() - start_time))
