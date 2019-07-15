import os
import shutil


def create_tradeterminal():

    soucepath = os.path.join(os.path.dirname(__file__), "template/mytrade.py")
    destpath = os.path.join(os.getcwd(), "mytrade.py")
    if not os.path.exists(destpath):
        shutil.copy(soucepath, destpath)

    soucepath = os.path.join(os.path.dirname(__file__), "template/mt.ini")
    destpath = os.path.join(os.getcwd(), "mt.ini")
    if not os.path.exists(destpath):
        shutil.copy(soucepath, destpath)
