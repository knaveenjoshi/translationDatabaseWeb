import os
import glob
import re
import codecs
import datetime
from docutils.utils.smartquotes import smartyPants
import requests


# Regexes for splitting the chapter into components
TITLE_RE = re.compile(ur'======.*', re.UNICODE)
REF_RE = re.compile(ur'//.*//', re.UNICODE)
FRAME_RE = re.compile(ur'{{[^{]*', re.DOTALL | re.UNICODE)
FRID_RE = re.compile(ur'[0-5][0-9]-[0-9][0-9]', re.UNICODE)
NUM_RE = re.compile(ur'([0-5][0-9]).txt', re.UNICODE)

# Regexes for removing text formatting
HTML_TAG_RE = re.compile(ur'<.*?>', re.UNICODE)
LINK_TAG_RE = re.compile(ur'\[\[.*?\]\]', re.UNICODE)
IMG_TAG_RE = re.compile(ur'{{.*?}}', re.UNICODE)
IMG_LINK_RE = re.compile(ur'https://.*\.(jpg|jpeg|gif)', re.UNICODE)

# Regexes for front matter
OBS_NAME_RE = re.compile(ur'\| (.*)\*\*', re.UNICODE)
TAG_LINE_RE = re.compile(ur'\n\*\*.*openbiblestories', re.UNICODE | re.DOTALL)

# OBS Defaults
OBS_DEFAULT_NAME = 'Open Bible Stories'
OBS_DEFAULT_TAGLINE = 'an unrestricted visual mini-Bible in any language'
IMG_URL = 'https://api.unfoldingword.org/obs/jpg/1/{0}/360px/obs-{0}-{1}.jpg'
PAGES_URL_PATTERN = 'https://door43.org/{lang_code}/obs/{chapter}'
RAW_URL_PATTERN = "https://door43.org/{lang_code}/obs/{chapter}?do=export_raw"
RAW_BASE_URL = "https://door43.org/{lang_code}/obs?do=export_raw"
BASE_URL = "https://door43.org/{lang_code}/obs"


CHAPTER_LIST = ["{0:02}".format(x) for x in range(1,51)]

# OBS Frameset Definition
OBS_FRAMESET = {"01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07", "01-08", "01-09", "01-10", "01-11",
                "01-12", "01-13", "01-14", "01-15", "01-16", "02-01", "02-02", "02-03", "02-04", "02-05", "02-06",
                "02-07", "02-08", "02-09", "02-10", "02-11", "02-12", "03-01", "03-02", "03-03", "03-04", "03-05",
                "03-06", "03-07", "03-08", "03-09", "03-10", "03-11", "03-12", "03-13", "03-14", "03-15", "03-16",
                "04-01", "04-02", "04-03", "04-04", "04-05", "04-06", "04-07", "04-08", "04-09", "05-01", "05-02",
                "05-03", "05-04", "05-05", "05-06", "05-07", "05-08", "05-09", "05-10", "06-01", "06-02", "06-03",
                "06-04", "06-05", "06-06", "06-07", "07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07",
                "07-08", "07-09", "07-10", "08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08",
                "08-09", "08-10", "08-11", "08-12", "08-13", "08-14", "08-15", "09-01", "09-02", "09-03", "09-04",
                "09-05", "09-06", "09-07", "09-08", "09-09", "09-10", "09-11", "09-12", "09-13", "09-14", "09-15",
                "10-01", "10-02", "10-03", "10-04", "10-05", "10-06", "10-07", "10-08", "10-09", "10-10", "10-11",
                "10-12", "11-01", "11-02", "11-03", "11-04", "11-05", "11-06", "11-07", "11-08", "12-01", "12-02",
                "12-03", "12-04", "12-05", "12-06", "12-07", "12-08", "12-09", "12-10", "12-11", "12-12", "12-13",
                "12-14", "13-01", "13-02", "13-03", "13-04", "13-05", "13-06", "13-07", "13-08", "13-09", "13-10",
                "13-11", "13-12", "13-13", "13-14", "13-15", "14-01", "14-02", "14-03", "14-04", "14-05", "14-06",
                "14-07", "14-08", "14-09", "14-10", "14-11", "14-12", "14-13", "14-14", "14-15", "15-01", "15-02",
                "15-03", "15-04", "15-05", "15-06", "15-07", "15-08", "15-09", "15-10", "15-11", "15-12", "15-13",
                "16-01", "16-02", "16-03", "16-04", "16-05", "16-06", "16-07", "16-08", "16-09", "16-10", "16-11",
                "16-12", "16-13", "16-14", "16-15", "16-16", "16-17", "16-18", "17-01", "17-02", "17-03", "17-04",
                "17-05", "17-06", "17-07", "17-08", "17-09", "17-10", "17-11", "17-12", "17-13", "17-14", "18-01",
                "18-02", "18-03", "18-04", "18-05", "18-06", "18-07", "18-08", "18-09", "18-10", "18-11", "18-12",
                "18-13", "19-01", "19-02", "19-03", "19-04", "19-05", "19-06", "19-07", "19-08", "19-09", "19-10",
                "19-11", "19-12", "19-13", "19-14", "19-15", "19-16", "19-17", "19-18", "20-01", "20-02", "20-03",
                "20-04", "20-05", "20-06", "20-07", "20-08", "20-09", "20-10", "20-11", "20-12", "20-13", "21-01",
                "21-02", "21-03", "21-04", "21-05", "21-06", "21-07", "21-08", "21-09", "21-10", "21-11", "21-12",
                "21-13", "21-14", "21-15", "22-01", "22-02", "22-03", "22-04", "22-05", "22-06", "22-07", "23-01",
                "23-02", "23-03", "23-04", "23-05", "23-06", "23-07", "23-08", "23-09", "23-10", "24-01", "24-02",
                "24-03", "24-04", "24-05", "24-06", "24-07", "24-08", "24-09", "25-01", "25-02", "25-03", "25-04",
                "25-05", "25-06", "25-07", "25-08", "26-01", "26-02", "26-03", "26-04", "26-05", "26-06", "26-07",
                "26-08", "26-09", "26-10", "27-01", "27-02", "27-03", "27-04", "27-05", "27-06", "27-07", "27-08",
                "27-09", "27-10", "27-11", "28-01", "28-02", "28-03", "28-04", "28-05", "28-06", "28-07", "28-08",
                "28-09", "28-10", "29-01", "29-02", "29-03", "29-04", "29-05", "29-06", "29-07", "29-08", "29-09",
                "30-01", "30-02", "30-03", "30-04", "30-05", "30-06", "30-07", "30-08", "30-09", "31-01", "31-02",
                "31-03", "31-04", "31-05", "31-06", "31-07", "31-08", "32-01", "32-02", "32-03", "32-04", "32-05",
                "32-06", "32-07", "32-08", "32-09", "32-10", "32-11", "32-12", "32-13", "32-14", "32-15", "32-16",
                "33-01", "33-02", "33-03", "33-04", "33-05", "33-06", "33-07", "33-08", "33-09", "34-01", "34-02",
                "34-03", "34-04", "34-05", "34-06", "34-07", "34-08", "34-09", "34-10", "35-01", "35-02", "35-03",
                "35-04", "35-05", "35-06", "35-07", "35-08", "35-09", "35-10", "35-11", "35-12", "35-13", "36-01",
                "36-02", "36-03", "36-04", "36-05", "36-06", "36-07", "37-01", "37-02", "37-03", "37-04", "37-05",
                "37-06", "37-07", "37-08", "37-09", "37-10", "37-11", "38-01", "38-02", "38-03", "38-04", "38-05",
                "38-06", "38-07", "38-08", "38-09", "38-10", "38-11", "38-12", "38-13", "38-14", "38-15", "39-01",
                "39-02", "39-03", "39-04", "39-05", "39-06", "39-07", "39-08", "39-09", "39-10", "39-11", "39-12",
                "40-01", "40-02", "40-03", "40-04", "40-05", "40-06", "40-07", "40-08", "40-09", "41-01", "41-02",
                "41-03", "41-04", "41-05", "41-06", "41-07", "41-08", "42-01", "42-02", "42-03", "42-04", "42-05",
                "42-06", "42-07", "42-08", "42-09", "42-10", "42-11", "43-01", "43-02", "43-03", "43-04", "43-05",
                "43-06", "43-07", "43-08", "43-09", "43-10", "43-11", "43-12", "43-13", "44-01", "44-02", "44-03",
                "44-04", "44-05", "44-06", "44-07", "44-08", "44-09", "45-01", "45-02", "45-03", "45-04", "45-05",
                "45-06", "45-07", "45-08", "45-09", "45-10", "45-11", "45-12", "45-13", "46-01", "46-02", "46-03",
                "46-04", "46-05", "46-06", "46-07", "46-08", "46-09", "46-10", "47-01", "47-02", "47-03", "47-04",
                "47-05", "47-06", "47-07", "47-08", "47-09", "47-10", "47-11", "47-12", "47-13", "47-14", "48-01",
                "48-02", "48-03", "48-04", "48-05", "48-06", "48-07", "48-08", "48-09", "48-10", "48-11", "48-12",
                "48-13", "48-14", "49-01", "49-02", "49-03", "49-04", "49-05", "49-06", "49-07", "49-08", "49-09",
                "49-10", "49-11", "49-12", "49-13", "49-14", "49-15", "49-16", "49-17", "49-18", "50-01", "50-02",
                "50-03", "50-04", "50-05", "50-06", "50-07", "50-08", "50-09", "50-10", "50-11", "50-12", "50-13",
                "50-14", "50-15", "50-16", "50-17"}

OBS_SUB_DIR = 'obs'


def clean_text(input_text):
    """
    cleans up text from possible dokuwiki and html tag polution

    :param input_text:
    :return:
    """
    output_text = HTML_TAG_RE.sub(u'', input_text)
    output_text = LINK_TAG_RE.sub(u'', output_text)
    output_text = IMG_TAG_RE.sub(u'', output_text)
    return output_text


class OBSTranslation(object):
    def __init__(self, base_path="", lang_code=""):
        self.lang_code = lang_code
        self.base_path = base_path
        self.obs_path = os.path.join(self.base_path, self.lang_code, OBS_SUB_DIR)
        self.qa_issues_list = []
        self.qa_valid_flag = False
        self._qa_performed = False
        self.today = ''.join(str(datetime.date.today()).rsplit('-')[0:3])
        self.session = requests.session()

    def append_issue(self, description, chapter):
        self.qa_issues_list.append({"description": description,
                                    "url": PAGES_URL_PATTERN.format(lang_code=self.lang_code, chapter=chapter)})

    @staticmethod
    def get_img(link, frame_id):
        links = IMG_LINK_RE.search(link)
        if links:
            return links.group(0)
        else:
            return IMG_URL.format('en', frame_id)

    @staticmethod
    def get_frame_text(lines):
        text = u''.join([x for x in lines[1:] if u'//' not in x]).strip()
        text = text.replace(u'\\\\', u'').replace(u'**', u'').replace(u'__', u'')
        text = clean_text(text)
        text = smartyPants(text)
        return text

    def _get_chapter(self, chapter_number):
        chapter_data = {"frames": []}
        response = self.session.get(RAW_URL_PATTERN.format(lang_code=self.lang_code, chapter=chapter_number))
        response.encoding = "utf-8"
        if response.status_code != 200:
            self.append_issue("Chapter {0} is missing".format(chapter_number), chapter_number)
        else:
            chapter_raw = response.text
            titles = TITLE_RE.search(chapter_raw)
            if titles:
                chapter_data['title'] = titles.group(0).replace('=', '').strip()
            else:
                chapter_data['title'] = u'NOT FOUND'
                self.append_issue(u"NOT FOUND: title in chapter {0}".format(chapter_number), chapter_number)
            refs = REF_RE.search(chapter_raw)
            if refs:
                chapter_data['ref'] = refs.group(0).replace('/', '').strip()
            else:
                chapter_data['ref'] = u'NOT FOUND'
                self.append_issue(u"NOT FOUND: reference in {0}".format(chapter_number), chapter_number)
            for frame in FRAME_RE.findall(chapter_raw):
                frame_lines = frame.split('\n')
                frame_ids = FRID_RE.search(frame)
                if frame_ids:
                    frame_id = frame_ids.group(0)
                else:
                    frame_id = u"NOT FOUND"
                    self.append_issue(u"NOT FOUND: frame id in {0}".format(chapter_number), chapter_number)
                frame_data = {"id": frame_id,
                              "img": self.get_img(frame_lines[0].strip(), frame_id),
                              "text": self.get_frame_text(frame_lines[1:])
                              }
                chapter_data["frames"].append(frame_data)
        return chapter_data

    def _get_front_matter(self):
        front_data = {}
        # todo: redo all this using requests
        # front_path = os.path.join(self.obs_path, "front-matter.txt")
        # if os.path.exists(front_path):
        #    front_matter = codecs.open(front_path, 'r', encoding='utf-8').read()
        #    obs_names = OBS_NAME_RE.search(front_matter)
        #    if obs_names:
        #        front_data["name"] = obs_names.group(1)
        #    else:
        #        front_data["name"] = OBS_DEFAULT_NAME
        #    tag_lines = TAG_LINE_RE.search(front_matter)
        #    if tag_lines:
        #        front_data["tagline"] = tag_lines.group(0).split('**')[1].strip()
        #    else:
        #        front_data["tagline"] = OBS_DEFAULT_TAGLINE
        #    front_data["language"] = self.lang_code
        #    front_data["date_modified"] = self.today
        #    front_data["front-matter"] = clean_text(front_matter)
        return front_data

    def _get_back_matter(self):
        back_data = {}
        # todo: redo all this using requests
        # back_path = os.path.join(self.obs_path, "back-matter.txt")
        # if os.path.exists(back_path):
        #    back = codecs.open(back_path, 'r', encoding='utf-8').read()
        #    back_data["language"] = self.lang_code
        #    back_data["back-matter"] = clean_text(back)
        #    back_data["date_modified"] = datetime.date.today()
        return back_data

    def _get_chapters(self):
        chapter_list = []
        for cn in CHAPTER_LIST:
            chapter_data = {"number": cn,
                            "chapter_data": self._get_chapter(cn)
                            }
            chapter_list.append(chapter_data)
        return chapter_list

    def check_frames(self):
        frame_set = set()
        for c in self._get_chapters():
            for f in c["chapter_data"]["frames"]:
                if len(f["text"]) > 10:
                    frame_set.add(f["id"])
        obs_diff = OBS_FRAMESET.difference(frame_set)
        for d in obs_diff:
            self.append_issue("missing frame: {0}".format(d), d[0:2])

    def _check_index_page(self):
        response = self.session.get(RAW_BASE_URL.format(lang_code=self.lang_code))
        if response.status_code != 200:
            self.append_issue("OBS does not seem to exist for that language", "")
            return False
        return True

    def qa_check(self):
        self._qa_performed = True
        if self._check_index_page():
            self.check_frames()
        self.qa_valid_flag = True if not len(self.qa_issues_list) else False
        return self.qa_valid_flag

    def publish(self):
        pass

    def __str__(self):
        return "OBS Translation for: {0}".format(self.lang_code)
