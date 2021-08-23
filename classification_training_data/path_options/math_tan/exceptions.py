'''
    File name: exceptions.py
    Author: Nidhin
    Origin: https://github.com/BehroozMansouri/TangentCFT
'''

__author__ = 'Nidhin'


class UnknownTagException(Exception):
    """
    An exception to indicate unknown Mathml tag
    """

    def __init__(self, tag):
        self.tag = tag
