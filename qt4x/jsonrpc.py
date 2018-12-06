# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
'''
轻量级的JSON-RPC 2.0客户端和服务器

简单实现，目前暂不支持notify模式、batch调用
'''

from __future__ import print_function, unicode_literals, absolute_import

import SocketServer
import SimpleXMLRPCServer
import BaseHTTPServer
import json
import string
import urllib2
import urllib
import random
import socket
import errno
import traceback
import select
import logging
import time
import struct
import sys

logger = logging.getLogger("JsonRPC")

IDCHARS = string.ascii_lowercase + string.digits

def random_id(length=8):
    return_id = ''
    for _ in range(length):
        return_id += random.choice(IDCHARS)
    return return_id

def _byteify(data, encoding):
    '''JSON结构中的字符串都转成对应的编码
    '''
    if isinstance(data, dict):
        dic={}
        for key,value in data.iteritems():
            dic[_byteify(key, encoding)]=_byteify(value, encoding)
        return dic
    elif isinstance(data, list):
        ls=[]
        for element in data:
            ls.append(_byteify(element, encoding))
        return ls
    elif isinstance(data, unicode):
        return data.encode(encoding)
    else:
        return data
    
    
class ProtocolError(Exception):
    '''协议实现相关错误
    '''
    pass

class Error(Exception):
    '''调用返回错误
    '''
    def __init__(self, code, message, data, stack=None ):
        '''Constructor
        
        :param code: 错误码
        :type code: int
        :param message: 错误消息
        :type message: string
        :param data: 错误扩展信息
        :type data: object
        '''
        if isinstance(message, unicode):
            message = message.encode('utf8')
        self.code = code
        self.message = message
        self.data = data
        if stack:
            if isinstance(stack, unicode):
                stack = stack.encode('utf8')
            super(Error, self).__init__("[code=%s] %s\n" % (self.code, self.message) + self.DEBUG_INFO % stack)
        else:
            super(Error, self).__init__("[code=%s] %s" % (self.code, self.message))

    DEBUG_INFO = """
------------------------------------------------------
*                                                    *
*    DEBUG INFORMATION:                              *
*                                                    *
------------------------------------------------------
%s
"""

class ParseError(Error):
    '''解析请求包错误
    '''
    PREDEFINE_CODE = -32700
    def __init__(self, message, data, stack=None ):
        super(ParseError, self).__init__(self.PREDEFINE_CODE, message, data)
        
class InvalidRequestError(Error):
    '''解析请求包结构错误
    '''
    PREDEFINE_CODE = -32600
    def __init__(self, message, data, stack=None ):
        super(InvalidRequestError, self).__init__(self.PREDEFINE_CODE, message, data)
        
class MethodNotFoundError(Error):
    '''方法不存在
    '''
    PREDEFINE_CODE = -32601
    def __init__(self, message, data, stack=None ):
        super(MethodNotFoundError, self).__init__(self.PREDEFINE_CODE, message, data)

class InvalidParamsError(Error):
    '''调用方法的参数错误
    '''
    PREDEFINE_CODE = -32602
    def __init__(self, message, data, stack=None ):
        super(InvalidParamsError, self).__init__(self.PREDEFINE_CODE, message, data)
    
class InternalError(Error):
    '''JSON-RPC内部错误
    '''
    PREDEFINE_CODE = -32603
    def __init__(self, message, data, stack=None ):
        super(InternalError, self).__init__(self.PREDEFINE_CODE, message, data, stack)
    
PREDEFINE_ERRORS = {
    ParseError.PREDEFINE_CODE: ParseError,
    InvalidRequestError.PREDEFINE_CODE: InvalidRequestError,
    MethodNotFoundError.PREDEFINE_CODE: MethodNotFoundError,
    InvalidParamsError.PREDEFINE_CODE: InvalidParamsError,
    InternalError.PREDEFINE_CODE: InternalError
}

class ServerError(Error):
    '''服务器相关错误
    '''
    CODE_MAX = -32000
    CODE_MIN = -32099
    
class HTTPTransport(object):
    '''处理请求到HTTP服务器
    '''
    def __init__(self):
        '''constructor
        '''
        self._timeout = None
        proxy_handler = urllib2.ProxyHandler({})       
        proxy_auth_handler = urllib2.HTTPBasicAuthHandler()     
        self._opener = urllib2.build_opener(proxy_handler, proxy_auth_handler)
        
    def close(self):
        '''关闭连接
        '''
        self._opener.close()
        
    def settimeout(self, timeout ):
        '''设置请求超时时间
        
        :param timeout: 超时时间
        :type timeout: int
        '''
        self._timeout = timeout

    def request(self, uri, request ):
        '''发送请求
        
        :param uri: 目标
        :type uri: string
        :param request: 请求包
        :type request: string
        :returns: string
        '''
        req = urllib2.Request(uri, request, {"Content-Type": "application/json-rpc"})
        return self._opener.open(req, timeout=self._timeout).read()
    
class _Method(object):
    '''some magic to bind an JSON-RPC method to an RPC server.
    supports "nested" methods (e.g. examples.getStateName)
    '''
    def __init__(self, send, name):
        self.__send = send
        self.__name = name
    def __getattr__(self, name):
        return _Method(self.__send, "%s.%s" % (self.__name, name))
    def __call__(self, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise ProtocolError('Cannot use both positional ' +
                'and keyword arguments (according to JSON-RPC spec.)')
        if len(args) > 0:
            return self.__send(self.__name, args)
        else:
            return self.__send(self.__name, kwargs)
    
class ServerProxy(object):
    '''和JSON-RPC服务器的逻辑连接
    '''
    def __init__(self, uri, transport=None, encoding="utf8", timeout=10):
        '''构造函数
        
        :param uri: RPC URL
        :type uri: string
        :param transport: 传输层
        :type transport: HTTPTransport/LongHTTPTransport
        :param encoding: 编码方式，默认为unicode
        :type encoding: string
        :param timeout: RPC请求超时时间
        :type timeout: int
        '''
        self.__uri = uri
        if transport is None:
            transport =  HTTPTransport()
        transport.settimeout(timeout)
        self.__transport = transport
        self.__encoding = encoding

    def __close(self):
        '''close connection to remote server
        '''
        self.__transport.close()

    def __request(self, methodname, params):
        '''call a method on the remote server
        '''
        request = {"jsonrpc": "2.0"}
        if len(params) > 0:
            request["params"] = params
        request["id"] = random_id()
        request["method"] = methodname
        response = self.__transport.request(
            self.__uri,
            json.dumps(request))
        
        response = json.loads(response)
        if self.__encoding:
            response = _byteify(response, self.__encoding)        
        if not isinstance(response, dict):
            raise ProtocolError('Response is not a dict.')
        
        if 'jsonrpc' in response.keys() and float(response['jsonrpc']) > 2.0:
            raise NotImplementedError('JSON-RPC version not yet supported.')
        
        if 'result' not in response.keys() and 'error' not in response.keys():
            raise ProtocolError('Response does not have a result or error key.')
        
        if 'error' in response.keys() and response['error'] != None:
            code = response['error']['code']
            err_cls = PREDEFINE_ERRORS.get(code, None)
            if err_cls:
                raise err_cls(response['error']['message'], 
                              response['error'].get('data',None),
                              response['error'].get('stack',None))
            if code < ServerError.CODE_MAX and code > ServerError.CODE_MIN:
                err_cls = ServerError
            else:
                err_cls = Error
            raise err_cls(response['error']['code'],
                          response['error']['message'], 
                          response['error'].get('data',None),
                          response['error'].get('stack',None))
        else:
            return response['result']

    def __repr__(self):
        return "<ServerProxy for %s>" % self.__uri

    __str__ = __repr__

    def __getattr__(self, name):
        '''magic method dispatcher
        note: to call a remote object with an non-standard name, use
        result getattr(server, "strange-python-name")(args)
        '''
        return _Method(self.__request, name)

    def __call__(self, attr):
        '''A workaround to get special attributes on the ServerProxy
           without interfering with the magic __getattr__
        '''
        if attr == "close":
            return self.__close
        elif attr == "transport":
            return self.__transport
        raise AttributeError("Attribute %r not found" % (attr,))

class SimpleJSONRPCDispatcher(object):
    '''简单的JSON-RPC分发器
    '''
    def __init__(self):
        '''Constructor
        '''
        self.funcs = {}
        self.instance = None
        
    def register_instance(self, instance, allow_dotted_names=False):
        '''注册一个对象去响应RPC请求
        '''
        self.instance = instance
        self.allow_dotted_names = allow_dotted_names
        
    def register_function(self, function, name=None):
        '''注册一个函数去响应RPC请求
        '''
        if name is None:
            name = function.__name__
        self.funcs[name] = function
        
    def _construct_error(self, reqid, code, msg, data=None, stack=None ):
        '''返回错误给客户端
        '''
        return json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": msg,
                "data": data,
                "stack": stack,
            },
            "id": reqid
        })
        
    def get_handler(self, method):
        '''获取对应的方法的处理句柄
        '''
        func = None
        try:
            #先检查已经注册的函数
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                #检查已经注册的实例的成员函数
                try:
                    func = SimpleXMLRPCServer.resolve_dotted_attribute(
                        self.instance,
                        method,
                        self.allow_dotted_names
                        )
                except AttributeError:
                    pass
        return func
    
    def marshaled_dispatch(self, data ):
        '''分发一个为序列化的RPC请求
        '''
        reqid = None
        try:
            try:
                req = json.loads(data)
            except ValueError:
                return self._construct_error(None, ParseError.PREDEFINE_CODE, "parse JSON data from request error")
    
            if not isinstance(req, dict):
                return self._construct_error(None, InvalidRequestError.PREDEFINE_CODE, "request should be a JSON object")
            
            if "id" not in req:
                return self._construct_error(None, InvalidRequestError.PREDEFINE_CODE, "notification is not supported")
            
            reqid = req["id"]
            
            if "jsonrpc" not in req:
                return self._construct_error(reqid, InvalidRequestError.PREDEFINE_CODE, "request field \"jsonrpc\" is missing")
            if req["jsonrpc"] != "2.0":
                return self._construct_error(reqid, InvalidRequestError.PREDEFINE_CODE, "unsupported version \"%s\"" % req["jsonrpc"])
            
            if "method" not in req:
                return self._construct_error(reqid, InvalidRequestError.PREDEFINE_CODE, "request field \"method\" is missing")
                
            func = self.get_handler(req["method"])
            if func is None:
                return self._construct_error(reqid, MethodNotFoundError.PREDEFINE_CODE, "supported method \"%s\"" % req["method"])
            
            params = req.get("params", [])
            if isinstance(params, dict):
                result = func(**params)
            elif isinstance(params, list):
                result = func(*params)
            else:
                return self._construct_error(reqid, InvalidRequestError.PREDEFINE_CODE, "request field \"params\" should be a list or object")
    
            return json.dumps({
                "jsonrpc": "2.0",
                "result": result,
                "id": reqid
            })
        except Exception, e:
            return self._construct_error(reqid, InternalError.PREDEFINE_CODE, 
                                         str(type(e).__name__) + ': ' + str(e), 
                                         None,
                                         traceback.format_exc())
            
            
            
class SimpleJSONRPCRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    '''简单的JSON-RPC HTTP请求处理句柄
    '''
    #合法的路径集
    rpc_paths = ('/', '/json', '/json/')

    def is_rpc_path_valid(self):
        '''检查路径合法性
        '''
        if self.rpc_paths:
            return self.path in self.rpc_paths
        else:
            #如果为空，则认为全部路径都是合法的
            return True

    def do_POST(self):
        """处理HTTP POST请求
        """
        if not self.is_rpc_path_valid():
            self.report_404()
            return

        try:
            # Get arguments by reading body of request.
            # We read this in chunks to avoid straining
            # socket.read(); around the 10 or 15Mb mark, some platforms
            # begin to have problems (bug #792570).
            max_chunk_size = 10*1024*1024
            size_remaining = int(self.headers["content-length"])
            L = []
            while size_remaining:
                chunk_size = min(size_remaining, max_chunk_size)
                L.append(self.rfile.read(chunk_size))
                size_remaining -= len(L[-1])
            data = ''.join(L)
            
            encoding = self.headers.get("content-encoding", "identity").lower()
            if encoding != "identity":
                self.send_response(501, "encoding %r not supported" % encoding)
                self.send_header("Content-length", "0")
                self.end_headers()
                return

            response = self.server.marshaled_dispatch(data)

        except Exception:  # 内部实现有问题
            self.send_response(500)
            self.send_header("Content-length", "0")
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json-rpc")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def report_404 (self):
        '''返回404错误
        '''
        self.send_response(404)
        response = 'No such page'
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_request(self, code='-', size='-'):
        '''记录请求
        '''
        if self.server.logRequests:
            BaseHTTPServer.BaseHTTPRequestHandler.log_request(self, code, size)
            
class SimpleJSONRPCServer(SocketServer.TCPServer,
                          SimpleJSONRPCDispatcher):
    '''简单的JSON-RPC服务器
    '''
    
    def __init__(self, addr, requestHandler=SimpleJSONRPCRequestHandler,
                 logRequests=True, bind_and_activate=True):
        self.logRequests = logRequests
        SimpleJSONRPCDispatcher.__init__(self)
        self.allow_reuse_address=True
        SocketServer.TCPServer.__init__(self, addr, requestHandler, bind_and_activate)
        
MAX_BUFSIZE=4096

class rpc_method():
    def __init__(self,func):
        self._func=func
    
    @property
    def func(self):
        return self._func
    
    def __call__(self,*argv,**kwargs):
        return self.func(*argv,**kwargs)

class TCPJsonRPCHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        recv_buf=""
        while 1:
            try:
                r,_,x=select.select([self.request],[],[self.request],1)
                if len(r)>0:
                    data=self.request.recv(MAX_BUFSIZE)
                    if data=="":
                        self.request.close()
                        break
                    recv_buf+=data
                    if recv_buf>=4:
                        expect_len=struct.unpack("!I",recv_buf[0:4])[0]
                        if len(recv_buf)>=expect_len:
                            real_data=json.loads(recv_buf[4:expect_len])#处理json转义
                            result=self.server.marshaled_dispatch(real_data)
                            self.request.send(struct.pack("!I",len(result)+4)+result)
                            recv_buf=recv_buf[expect_len:]
                        if self.server.logRequests:
                            logger.info("msg form %s:%s"  % (self.client_address,real_data))
                            logger.info("result:%s" % result)
                if len(x)>0:
                    self.request.close()
                    break
            except Exception as e:
                logger.info("error:%s",str(e))
                break
    
class UDPJsonRPCHandler(SocketServer.DatagramRequestHandler):
    def handle(self):
        data=self.packet[4:]
        real_data=json.loads(data)#处理json转义
        result=self.server.marshaled_dispatch(real_data)
        self.socket.sendto(struct.pack("!I",len(result)+4)+result,self.client_address)
        if self.server.logRequests:
            logger.info("msg form %s:%s"  % (self.client_address,real_data))
            logger.info("result:%s" % result)
        
class TCPJsonRPCServer(SocketServer.TCPServer,SimpleJSONRPCDispatcher):
    '''简单的JSON-RPC服务器
    '''
    
    def __init__(self, addr, requestHandler=TCPJsonRPCHandler,
                 logRequests=False, bind_and_activate=True):
        self.logRequests = logRequests
        SimpleJSONRPCDispatcher.__init__(self)
        for name in dir(requestHandler):
            item=getattr(requestHandler,name)
            if isinstance(item, rpc_method):
                self.register_function(item.func)
        self.allow_reuse_address=True
        SocketServer.TCPServer.__init__(self, addr, requestHandler, bind_and_activate)
        
        
    def stop(self):
        self.shutdown()
        
class UDPJsonRPCServer(SocketServer.UDPServer,SimpleJSONRPCDispatcher):
    '''简单的JSON-RPC服务器
    '''
    
    def __init__(self, addr, requestHandler=UDPJsonRPCHandler,
                 logRequests=False, bind_and_activate=True):
        self.logRequests = logRequests
        SimpleJSONRPCDispatcher.__init__(self)
        for name in dir(requestHandler):
            item=getattr(requestHandler,name)
            if isinstance(item, rpc_method):
                self.register_function(item.func)
        self.allow_reuse_address=True
        SocketServer.UDPServer.__init__(self, addr, requestHandler, bind_and_activate)
