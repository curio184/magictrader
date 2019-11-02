import json

import requests
from requests_oauthlib import OAuth1Session


class SlackMessenger:
    """
    Slackにメッセージを送信するクラス
    https://api.slack.com/methods
    """

    def __init__(self, slack_token: str, slack_channel: str, slack_username: str):

        self._slack_token = slack_token
        self._slack_channel = slack_channel
        self._slack_username = slack_username

    def send_message(self, message: str):
        """
        Slackにメッセージを送信します

        Parameters
        ----------
        message : str
            メッセージ
        """
        try:
            param = {
                "token": self._slack_token,
                "channel": self._slack_channel,
                "username": self._slack_username,
                "text": message
            }
            requests.post(url="https://slack.com/api/chat.postMessage", params=param)
        except Exception as ex:
            print(ex)

    def send_picture(self, message: str, file_path: str):
        """
        Slackに画像を送信します

        Parameters
        ----------
        message : str
            メッセージ
        file_path : str
            送信する画像のパス
        """
        try:
            with open(file_path, "rb") as file_content:
                files = {"file": file_content}
                param = {
                    "token": self._slack_token,
                    "channels": self._slack_channel,
                    "username": self._slack_username,
                    "filename": file_path,
                    "initial_comment": message,
                    "title": file_path
                }
                requests.post(url="https://slack.com/api/files.upload", params=param, files=files)
        except Exception as ex:
            print(ex)


class TwitterMessenger:
    """
    Twitterにメッセージを送信するクラス
    https://developer.twitter.com/en/apps
    """

    def __init__(self, consumer_key: str, consumer_secret: str, access_token: str, access_token_secret: str):

        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._access_token = access_token
        self._access_token_secret = access_token_secret

    def send_message(self, message: str):
        """
        Twitterに画像を送信します

        Parameters
        ----------
        message : str
            メッセージ
        """
        try:
            # authorize
            twitter = OAuth1Session(
                self._consumer_key,
                self._consumer_secret,
                self._access_token,
                self._access_token_secret
            )

            # resource url
            url = "https://api.twitter.com/1.1/statuses/update.json"

            # post message
            params = {"status": message}
            res_message = twitter.post(url, params=params)
            if res_message.status_code != 200:
                print("failed to post message. : {}".format(res_message.text))
                return
        except Exception as ex:
            print(ex)

    def send_picture(self, message: str, file_path: str):
        """
        Twitterにメッセージを送信します

        Parameters
        ----------
        message : str
            メッセージ
        file_path : str
            送信する画像のパス
        """
        try:
            # authorize
            twitter = OAuth1Session(
                self._consumer_key,
                self._consumer_secret,
                self._access_token,
                self._access_token_secret
            )

            # resource url
            url_media = "https://upload.twitter.com/1.1/media/upload.json"
            url_text = "https://api.twitter.com/1.1/statuses/update.json"

            # upload picture
            files = {"media": open(file_path, 'rb')}
            res_media = twitter.post(url_media, files=files)
            if res_media.status_code != 200:
                print("Failed to upload picture. : {}".format(res_media.text))
                return

            # get media_id
            media_id = json.loads(res_media.text)["media_id"]

            # post message with media_id
            params = {"status": message, "media_ids": [media_id]}
            res_message = twitter.post(url_text, params=params)
            if res_message.status_code != 200:
                print("failed to post message : {}".format(res_message.text))
                return
        except Exception as ex:
            print(ex)
