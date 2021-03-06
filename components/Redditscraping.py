# pylint: disable=W1401, C0301

import re
import urllib.request
from imghdr import what as img_type
from os import path, makedirs, rename
from random import randint
from feedparser import parse as feedparser

ENTRIES_NAME = "entries"
SUMMARY_NAME = "summary"
TITLE_NAME = "title"

class Redditscraping:
    """ Class built for ripping imgur images from a reddit feed (rss) """

    def __init__(self, client):
        self.client = client
        self.i = 1
        self.image_count = 1

        if self.client.type not in ['random', 'standard', 'name']:
            self.client.type = "standard"

        if not path.exists(self.client.location):
            makedirs(self.client.location)

    def handle_errors(self, error_code, error, extra):
        """ handles errors that occure while scraping Reddit """

        if error_code == 1:
            print("Failed to download image: {image}, error: {error}".format(image=extra, error=str(error)))

    def image_exists(self, image_path):
        """ Returns true or false depending on if the file exists or not """

        supported_formats = ["jpeg", "png", "gif", "apng", "tiff", "pdf", "xcf"]

        for format_type in supported_formats:
            if path.exists("{file_path}.{type}".format(file_path=image_path, type=format_type)):
                return True
        return False

    def gather_reddit_rss(self, room):
        """ will a room name and limit, while then gathering the rss food upto that limit """

        page_types = ["hot", "new", "rising", "controversial", "top"]

        if self.client.page_type is not "hot" and self.client.page_type in page_types:
            reddit_url = "https://www.reddit.com/r/{room}/{page_type}/.rss?limit={limit}&after=0".format(room=room, page_type=self.client.page_type, limit=str(self.client.limit))
        else:
            reddit_url = "https://www.reddit.com/r/{room}/.rss?limit={limit}&after=0".format(room=room, limit=str(self.client.limit))

        feed = feedparser(reddit_url)
        return feed

    def parse_imgur_links(self, entry_summary):
        """ This will take in the reddit entry summary, parsing out the imgur links out of the summary text """

        if re.search("(?P<url>https?://imgur.com/([A-z0-9/-]+))(\?[[^/]+)?", entry_summary):
            imgururl = re.search("(?P<url>https?://imgur.com/([A-z0-9/-]+))(\?[[^/]+)?", entry_summary)
            imgururl = "http://i.{}.jpeg".format(imgururl.group(0)[7:])
            return imgururl
        elif re.search("(?P<url>https?://i.imgur.com/([A-z0-9\-]+))(\?[[^/]+)?", entry_summary):
            imgururl = re.search("(?P<url>https?://i.imgur.com/([A-z0-9\-]+))(\?[[^/]+)?", entry_summary)
            return "{}.jpeg".format(imgururl.group(0))
        else:
            return ''

    def download_image(self, url, room, name):
        """ This will take in the url, room and name, downloading the image from the url and print """
        if not self.image_exists(name):
            print("Downloading image room:  r/{subreddit}, {index}/{image_count}".format(subreddit=room, index=str(self.i), image_count=str(self.image_count)))
            try:
                urllib.request.urlretrieve(url, name)
                file_type = img_type(name)

                if str(file_type).lower() != "none":
                    rename(name, "{file_name}.{file_format}".format(file_name=name, file_format=file_type))
                else:
                    rename(name, "{file_name}.{file_format}".format(file_name=name, file_format="jpeg"))

                self.i += 1
            except (urllib.request.HTTPError, Exception) as err:
                self.handle_errors(1, err, url)
        else:
            print("Not downloading image room: r/{subreddit}, {index}/{image_count} - It already exists".format(subreddit=room, index=str(self.i), image_count=str(self.image_count)))

    def gather_images(self):
        """ goes through the provided array of rooms (sub reddits) and begin parsing and downloading any imgur links """

        for sub in self.client.rooms:
            current_feed = self.gather_reddit_rss(sub)
            entries_len = len(current_feed[ENTRIES_NAME])
            random_numbers = []

            for index, entry in enumerate(current_feed[ENTRIES_NAME]):
                imgur_url = self.parse_imgur_links(entry[SUMMARY_NAME])
                image_title = re.sub('[^A-Za-z0-9 ]+', '', str(entry[TITLE_NAME]))

                if"gallery" in imgur_url:
                    print("Galleries are not handled due to requiring Oauth 2.0: {}".format(imgur_url))
                    imgur_url = ''

                #random, name and standard are options that are pulled and transfered from the settings.ini file (will affect the naming of the files)
                if self.client.type == "random":
                    selected_number = randint(0, self.client.max_random_numbers)

                    while selected_number in random_numbers:
                        selected_number = randint(0, self.client.max_random_numbers)

                    random_numbers.append(selected_number)
                    file_name = "{location}[{room}] {name}".format(location=self.client.location, name=str(selected_number), room=sub)

                if self.client.type == "name":
                    file_name = "{location}[{room}] {name}".format(location=self.client.location, name=str(image_title), room=sub)

                if self.client.type == "standard":
                    file_name = "{location}[{room}] #{name}".format(location=self.client.location, name=str(self.image_count), room=sub)

                if imgur_url != '':
                    self.image_count += 1
                    self.download_image(imgur_url, sub, file_name)
                if index >= entries_len:
                    print("Downloading Complete in subreddit: {}".format(sub))

        return True
