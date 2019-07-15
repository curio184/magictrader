import requests


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

    def send_file(self, message: str, file_path: str):
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
