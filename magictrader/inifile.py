import codecs
import os
from configparser import ConfigParser


class INIFile:
    """
    INIファイルを読み書きするクラス
    """

    def __init__(self, filepath: str):
        """
        Parameters
        ----------
        filepath : str
            INIファイルのパス
        """
        self._filepath = filepath
        if os.path.exists(filepath):
            self._config = ConfigParser()
            self._config.readfp(codecs.open(filepath, "r", "utf8"))
        else:
            raise Exception("INI file doesn't exist. ({})".format(self._filepath))

    def get_str(self, section: str, key: str, default: str = "") -> str:
        """
        INIファイルの設定値(str)を取得する

        Parameters
        ----------
        section : str
            セクション名
        key : str
            キー名
        default : str, optional
            既定値, by default ""

        Returns
        -------
        str
            設定値
        """
        try:
            return self._config.get(section, key)
        except:
            return default

    def get_int(self, section: str, key: str, default: int = 0) -> int:
        """
        INIファイルの設定値(int)を取得する

        Parameters
        ----------
        section : str
            セクション名
        key : str
            キー名
        default : int, optional
            既定値, by default 0

        Returns
        -------
        int
            設定値
        """
        try:
            return self._config.getint(section, key)
        except:
            return default

    def get_float(self, section: str, key: str, default: float = 0.0) -> float:
        """
        INIファイルの設定値(float)を取得する

        Parameters
        ----------
        section : str
            セクション名
        key : str
            キー名
        default : float, optional
            既定値, by default 0.0

        Returns
        -------
        int
            設定値
        """
        try:
            return self._config.getfloat(section, key)
        except:
            return default

    def get_bool(self, section: str, key: str, default: bool = False) -> bool:
        """
        INIファイルの設定値(bool)を取得する

        Parameters
        ----------
        section : str
            セクション名
        key : str
            キー名
        default : bool, optional
            既定値, by default False

        Returns
        -------
        int
            設定値
        """
        try:
            return self._config.getboolean(section, key)
        except:
            return default

    def get_section(self, section: str) -> dict:
        return dict(self._config.items(section))

    @property
    def filepath(self) -> str:
        """
        INIファイルのパス
        """
        return self._filepath
