# -*- coding: utf-8 -*-
"""
Created on Tue Apr 05 16:58:08 2016

@author: Feng-cong Li
"""

from __future__ import print_function, division, unicode_literals

import os
import re
import collections
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
    IO Commands:
        read_from_file: read a PDF file, arguments: filename, return a stream;
        write_to_file: write to a PDF file, arguments: filename.
    Manipulation Commands:
        append: append one or more PDF files to the end of the current stream;
            arguments: filelist (the list of the PDF file names);
        remove_pages: remove pages from the stream, 
            arguments: pagenum (the number of the pages which will be removed);
        remove_annotations: remove the annotations of the current stream.

Command Pipeline Example:
[
    ('read_from_file', 'c:\\lab\\test0.pdf'),
    ('append', 'c:\\lab\\test1.pdf'),
    ('remove_annotations',),
    ('write_to_file', 'c:\\lab\\test2.pdf')
]
  '''
    def __init__(self):
        pass
    
    
    def execute(self, commands):
        read_command = commands[0]
        write_command = commands[-1]
        actions = commands[1:-1]
        
        input_file = output_file = None        
        
        if read_command[0] == 'read_from_file':
            path = os.path.abspath(read_command[1])
            input_file = _gateway.jvm.java.io.FileInputStream(path)
        else:
            raise NotImplementedError('The command is not implemented.')
            
        if write_command[0] == 'write_to_file':
            path = os.path.abspath(write_command[1])
            output_file = _gateway.jvm.java.io.FileOutputStream(path)
        else:
            raise NotImplementedError('The command is not implemented.')
            
        num_actions = len(actions)        
        input_stream = None
        output_stream = None
        
        command_dict = {}
        
        def append(input_stream, output_stream, *tail_files):
            input_streams = [input_stream]
            for tail_file in tail_files:
                input_streams.append(_gateway.jvm.java.io.FileInputStream(tail_file))
            self._merge(input_streams, output_stream)
            
        command_dict['append'] = append
        command_dict['remove_pages'] = self._remove_pages
        command_dict['remove_annotations'] = self._remove_annotations
                        
        try:
            for index, action in enumerate(actions):
                if index == 0: # The first action, input_stream from FileInputStream
                    input_stream = input_file            
                else: # Not the first action, input_stream from its previous action's output.
                    input_stream.close()
                    input_stream = _gateway.jvm.java.io.ByteArrayInputStream(output_stream.toByteArray())
                    output_stream.close()
    
                if index + 1 == num_actions: # The last action, output_stream is FileOutputStream.
                    output_stream = output_file
                else: # Not the last action, output_stream is an ByteArrayOutputStream.
                    output_stream = _gateway.jvm.java.io.ByteArrayOutputStream()
                    
                action_name = action[0]
                command_dict[action_name](input_stream, output_stream, *action[1:])
        finally:
            if input_file is not None:
                input_file.close()
            if output_file is not None:
                output_file.close()
    
    
    def _merge(self, input_streams, output_stream):
        document = pdfcopy = reader = None
        
        try:
            document = _gateway.jvm.com.itextpdf.text.Document()
            pdfcopy = _gateway.jvm.com.itextpdf.text.pdf.PdfCopy(document, output_stream)
            document.open()
            
            for input_stream in input_streams:
                reader = _gateway.jvm.com.itextpdf.text.pdf.PdfReader(input_stream)
                for n in range(reader.getNumberOfPages()):
                    pdfcopy.addPage(pdfcopy.getImportedPage(reader, n+1))
                reader.close()
                reader = None
        finally:
            if document is not None and document.isOpen():
                document.close()
            if pdfcopy is not None:
                pdfcopy.close()
            if reader is not None:
                reader.close()
                
                
    def _remove_pages(self, input_stream, output_stream, page_num):
        if not isinstance(page_num, collections.Iterable):
            page_num = [page_num]
        page_num = set(page_num)
        
        document = pdfcopy = reader = None
        
        try:
            document = _gateway.jvm.com.itextpdf.text.Document()
            pdfcopy = _gateway.jvm.com.itextpdf.text.pdf.PdfCopy(document, output_stream)
            document.open()
            
            reader = _gateway.jvm.com.itextpdf.text.pdf.PdfReader(input_stream)
            for n in range(reader.getNumberOfPages()):
                if (n+1) not in page_num:
                    pdfcopy.addPage(pdfcopy.getImportedPage(reader, n+1))
                # else skip the page.
        finally:
            if reader is not None: reader.close()
            if pdfcopy is not None: pdfcopy.close()
            if document is not None: document.close()
                
                
    def _remove_annotations(self, input_stream, output_stream):
        reader = stamper = None
        try:
            reader = _gateway.jvm.com.itextpdf.text.pdf.PdfReader(input_stream)
            stamper = _gateway.jvm.com.itextpdf.text.pdf.PdfStamper(reader, output_stream)
            reader.removeAnnotations()
        finally:
            if stamper is not None:
                stamper.close()
            if reader is not None:
                reader.close()
        return output_stream
        
    

    