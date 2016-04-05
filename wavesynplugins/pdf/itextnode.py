# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 16:58:08 2016

@author: Feng-cong Li
"""

from __future__ import print_function, division, unicode_literals

import os
import re
from py4j.java_gateway import JavaGateway

from wavesynlib.languagecenter.utils import get_caller_dir


itext_filename = None
self_dir = get_caller_dir()

for filename in os.listdir(self_dir):
    if re.match('itextpdf.*\.jar', filename): # iText jar is found.
        itext_filename = os.path.join(self_dir, filename)
        
if itext_filename is None:
    raise ImportError('Cannot find iText jar file.')
    
_gateway = JavaGateway.launch_gateway(die_on_exit=True, classpath=itext_filename)

class PdfManipulator(object):
    '''
Supported Commands:
  '''
    def __init__(self):
        pass
    
    