# -*- coding:utf-8 -*-
from ast import literal_eval
from autoTest.models import Project, Environment, Api, TestStep, TestCases, Report, Encryption
import base64
import codecs
from decorator import decorator
import httprunner
import hmac
import hashlib
import logging
from multiprocessing import Pool
import os
import pprint
import requests
import random
import string
import time
import re
import requests


hrun_base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), r'httprunner\tests\testcases')


def run_Case():
    file_path = 'hrun ' + r'E:\github\djangoProject\testGoFunction\自动生成的案例.json'
    content = os.system(file_path)


def wpt_encode():
    key = '6f4965f5d8bc1010ff67ca792e335f67'
    operator = 'WUDLB'
    AppID = 'WPT-test'    #开发环境：WPT-dev(不做校验), 测试环境：WPT-test, 生产环境：WPT-production
    AppID_md5 = hashlib.md5(AppID.encode('utf-8')).hexdigest().encode('utf-8')
    SerialNo = ''
    for i in range(8):
        SerialNo  = SerialNo + random.choice(string.ascii_letters)
    Timestamp = str(time.time())[:10]
    resource_string = (AppID + SerialNo + Timestamp)
    resource_string_bytes  = resource_string.encode('utf-8')
    Signature = hmac.new(AppID_md5,resource_string_bytes,hashlib.sha1).digest()
    print('SerialNo: ',SerialNo)
    print('Timestamp: ',Timestamp)
    print('Signature: ',base64.b64encode(Signature))

def check_listFormat(getString):
    '''
    检测参数是否为[ ]格式，以"["开头, 以"]"结尾，若不是则补充[ 或 ]
    :param getString: 待检测字符串
    :return: 修改完的字符串
    '''
    if not getString:
        getString = '[]'
    else:
        if not getString.startswith('['):
            getString = '[' + getString
        if not getString.endswith(']'):
            getString = getString + ']'
    return getString

def replace_chinese_brackets(getString):
    '''
    将字符串内的中文括号（）,转化为英文括号()
    :param getString: 待检测字符串
    :return: 修改完的字符串
    '''
    getString.replace('（', '(')
    getString.replace('）', ')')
    return getString

def changeHookFormat(getString):
    '''
    将setup_hooks和teardown_hooks函数的格式
    由"[${hook_print(setup)}, ${hook2()}]" ==> ["${hook_print(setup)}", "${hook2()}"]
    :param getString: 
    :return: list
    '''
    getString = getString.replace('${', '"${')
    getString = getString.replace('}', '}"')
    eval_value = literal_eval(getString)
    if isinstance(eval_value,list):
        return eval_value
    else:
        return getString

def changeParametersFormat(testCasesObject):
    '''
    将parametersList根据指定的数据类型做转化
    :param testCasesObject: testCasesObject数据库对象实例
    :return: 转化后的parametersList列表
    '''
    parameters_begin = literal_eval(testCasesObject.parameters)
    parameters_dataType_list = literal_eval(testCasesObject.dataType_dict)['parameters']
    parameters_final = []
    index = 0
    for item in parameters_begin:
        dataType = parameters_dataType_list[index]
        cur_key = list(item.keys())[0]
        cur_value = list(item.values())[0]
        try:
            if dataType == 'string':
                cur_value = str(cur_value)
            if dataType == 'int':
                cur_value = int(float(cur_value))
            if dataType == 'double':
                cur_value = float(cur_value)
            if dataType == 'list':
                if cur_value.startswith('[') and cur_value.endswith(']'):
                    cur_value = literal_eval(cur_value)
                else:
                    cur_value = list(cur_value)
            if dataType == 'dict':
                if cur_value.startswith('{') and cur_value.endswith('}'):
                    cur_value = literal_eval(cur_value)
        except:
            print('parameters转换报错: ',cur_value, ' => ', dataType, '格式')
        parameters_final.append({cur_key:cur_value})
        index = index + 1
    return parameters_final

def changeVariablesFormat(testCasesObject):
    '''
    将variablesList根据指定的数据类型做转化
    :param testCasesObject: testCasesObject数据库对象实例 或 testStep数据库对象实例
    :return: 转化后的variablesList列表
    '''
    variables_begin = literal_eval(testCasesObject.variables)
    variables_dataType_list = literal_eval(testCasesObject.dataType_dict)['variables']
    variables_final = []
    index = 0
    for item in variables_begin:
        dataType = variables_dataType_list[index]
        cur_key = list(item.keys())[0]
        cur_value = list(item.values())[0]
        try:
            if dataType == 'string':
                cur_value = str(cur_value)
            if dataType == 'int':
                cur_value = int(float(cur_value))
            if dataType == 'double':
                cur_value = float(cur_value)
            if dataType == 'list':
                if cur_value.startswith('[') and cur_value.endswith(']'):
                    cur_value = literal_eval(cur_value)
                else:
                    cur_value = list(cur_value)
            if dataType == 'dict':
                if cur_value.startswith('{') and cur_value.endswith('}'):
                    cur_value = literal_eval(cur_value)
        except:
            print('variables转换报错: ',cur_value, ' => ', dataType, '格式')
        variables_final.append({cur_key:cur_value})
        index = index + 1
    return variables_final

def changeHeadersFormat(testCasesObject, headerString=''):
    '''
    将headersList根据指定的数据类型做转化
    :param testCasesObject: testCasesObject数据库对象实例
    :return: 转化后的headersDict字典
    '''
    index = 0
    headers_dict = {}
    headers_dataType_list = literal_eval(testCasesObject.dataType_dict)['headers']
    headers_loop = ''
    if headerString:
        headers_loop = headerString
    else:
        headers_loop = testCasesObject.headers
    for key,value in literal_eval(headers_loop).items():
        dataType = headers_dataType_list[index]
        try:
            if dataType == 'string':
                value = str(value)
            if dataType == 'int':
                value = int(float(value))
            if dataType == 'double':
                value = float(value)
            if dataType == 'list':
                if value.startswith('[') and value.endswith(']'):
                    value = literal_eval(value)
                else:
                    value = list(value)
            if dataType == 'dict':
                if value.startswith('{') and value.endswith('}'):
                    value = literal_eval(value)
        except:
            print('headers转换报错: ',value, ' => ', dataType, '格式')
        headers_dict.update({key:value})
        index = index + 1
    return headers_dict

def changeValidateFormat(testStepObject):
    '''
    将validateList根据指定的数据类型做转化
    :param testStepObject: testStep数据库对象实例
    :return: 转换后的validateList列表
    '''
    validate_dataType_list = literal_eval(testStepObject.dataType_dict)['validate']
    validate_begin = literal_eval(testStepObject.validate)
    validate_final = []
    index = 0
    for item in validate_begin:
        dataType = validate_dataType_list[index]
        item_key = list(item.keys())[0]
        item_value_list = list(item.values())[0]
        try:
            if dataType == 'string':
                item_value_list[1] = str(item_value_list[1])
            if dataType == 'int':
                item_value_list[1] = int(float(item_value_list[1]))
            if dataType == 'double':
                item_value_list[1] = float(item_value_list[1])
            if dataType == 'list':
                if item_value_list[1].startswith('[') and item_value_list[1].endswith(']'):
                    item_value_list[1] = literal_eval(item_value_list[1])
                else:
                    item_value_list[1] = list(item_value_list[1])
            if dataType == 'dict':
                if item_value_list[1].startswith('{') and item_value_list[1].endswith('}'):
                    item_value_list[1] = literal_eval(item_value_list[1])
        except:
            print('validate转换报错: ',item_value_list[1], ' => ', dataType, '格式')
        validate_final.append({item_key:item_value_list})
        index = index + 1
    return validate_final

def changeBodyFormat(testStepObject, bodyString=''):
    '''
    将bodyDict根据指定的数据类型做转化
    :param testStepObject: testStepObject数据库对象实例
    :return: 转化后的headersDict字典
    '''
    index = 0
    body_dict = {}
    body_dataType_list = literal_eval(testStepObject.dataType_dict)['body']
    body_loop = ''
    if bodyString:
        body_loop = bodyString
    else:
        body_loop = testStepObject.body
    for key, value in literal_eval(body_loop).items():
        dataType = body_dataType_list[index]
        try:
            if dataType == 'string':
                value = str(value)
            if dataType == 'int':
                value = int(float(value))
            if dataType == 'double':
                value = float(value)
            if dataType == 'list':
                if value.startswith('[') and value.endswith(']'):
                    value = literal_eval(value)
                else:
                    value = list(value)
            if dataType == 'dict':
                if value.startswith('{') and value.endswith('}'):
                    value = literal_eval(value)
        except:
            print('body转换报错: ', value, ' => ', dataType, '格式')
        body_dict.update({key: value})
        index = index + 1
    return body_dict

def decodeChinese(getString):
    '''
    将中文乱码字符串转为中文"itemName\\xe7\\xad\\x89\\xe9\\xa2\\x9d\\xe8\\xbf\\x98\\xe6\\xac\\xbe" ==>  'itemName等额还款'
    :param getString: 中文乱码string
    :return: 中文string
    '''
    utf8_pattern = re.compile(r"(\...\...\...|\\...\\...\\...)")
    if re.search(utf8_pattern, getString):
        return str(literal_eval(getString).decode('utf-8'))
    else:
        return getString

def createJsonFile(testCasesObject):
    '''
    生成httprunner测试用例.json文件
    :param testCasesObject: testCases数据库对象实例
    :return: 文件路径
    '''
    # parameters_begin = testCasesObject.parameters
    # parameters_final = []
    # for item in literal_eval(parameters_begin):
    #     try:
    #         temp_value = list(item.values())[0]
    #         if isinstance(literal_eval(temp_value), list):
    #             parameters_final.append({list(item.keys())[0]:literal_eval(temp_value)})
    #         else:
    #             parameters_final.append(item)
    #     except:
    #         parameters_final.append(item)
    test_list = [{"config": {"name": testCasesObject.testCases_name,
                             "parameters": changeParametersFormat(testCasesObject),
                             "variables": changeVariablesFormat(testCasesObject),
                             "request": {"headers": changeHeadersFormat(testCasesObject)},
                             "setup_hooks": changeHookFormat(testCasesObject.setup_hooks),
                             "teardown_hooks": changeHookFormat(testCasesObject.teardown_hooks),
                             "output": literal_eval(testCasesObject.output)
                             }},
                 ]
    testCases_list = literal_eval(testCasesObject.testCases_list)
    for testStep_id in testCases_list:
        testStepObject = TestStep.objects.get(testStep_id=testStep_id)
        data_param_name = ''
        if testStepObject.method.lower() == 'get':
            data_param_name = 'params'
        if testStepObject.method.lower() == 'post':
            if testStepObject.content_type.lower() == 'json':
                data_param_name = 'json'
            else:
                data_param_name = 'data'
        add_content = {"test": {"name": testStepObject.testStep_name,
                                # "skip": testStepObject.skip,
                                "skipIf": testStepObject.skipIf,
                                "skipUnless": testStepObject.skipUnless,
                                "times": testStepObject.times,
                                "variables": changeVariablesFormat(testStepObject),
                                "request": {"url": testStepObject.url,
                                            "method": testStepObject.method,
                                            "headers": changeHeadersFormat(testStepObject),
                                            data_param_name: changeBodyFormat(testStepObject),
                                            },
                                "extract": literal_eval(testStepObject.extract),
                                "validate": changeValidateFormat(testStepObject),
                                "setup_hooks": changeHookFormat(testStepObject.setup_hooks),
                                "teardown_hooks": changeHookFormat(testStepObject.setup_hooks)
                                }}
        if testStepObject.skip == 'True':
            add_content['test']['skip'] = 'True'
        test_list.append(add_content)
    # file_name = testCasesObject.testCases_name + '_' + str(time.time())[:10] + '.json'
    file_path = testCasesObject.file_path
    with open(file_path, 'w+',encoding='utf-8') as f:
        content = pprint.pformat(test_list).replace(r"'", r'"')
        f.write(content)
    print('测试用例文件自动生成成功：', file_path)
    return file_path
'''
@decorator
def multiprocess_pool(func, timelimit=300, *args, **kw):
    print('Run task (%s)...' % (os.getpid()))
    t0 = time.time()
    pool = Pool(4)
    result = pool.apply_async(func, args=args, kwds= kw)
    pool.close()
    pool.join()
    dt = time.time() - t0
    if dt > timelimit:
        logging.warning('%s took %d seconds', func.__name__, dt)
    else:
        logging.info('%s took %d seconds', func.__name__, dt)
    return result

@multiprocess_pool
def sleep():
    time.sleep(random.random() * 3)
'''
if __name__ == '__main__':
    # createJsonFile(ob)
    # run_Case()
    # wpt_encode()
    # pass
    # print(check_listFormat('123213dsfds'))
    pass