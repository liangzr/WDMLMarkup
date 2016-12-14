#! /usr/bin/python
# coding:utf-8

"""scan_opened_folder.py: scan all files to complete"""

__author__      = "Jory Liang"
__copyright__   = "Copyright 2016, ForTech"

import os
import re

# 存放所有的列表
rootList = []

# 匹配后缀
p = re.compile(r'^.*\.(\w+?)$')
# 匹配方法名
p_func = re.compile(r'[\n]function\s(.*\))')

# 扫描要求的文件夹
def scan_folder(root_dir):
    for lists in os.listdir(root_dir):
        # 跳过隐藏文件夹
        if lists[0] == ".":
            continue
        path = os.path.join(root_dir, lists)
        if os.path.isdir(path):
            scan_folder(path)
        elif os.path.isfile(path):
            handle_files(path)

def scan_folders(lists):
    clear_list()
    for folder in lists:
        scan_folder(folder)
    print(len(rootList))
    return rootList

def clear_list():
    del(rootList[:])

# 处理文件
def handle_files(path):
    if suffix_judge(path):
        try:
            with open(path, 'r', encoding="utf-8") as f:
                rootList.extend(p_func.findall(f.read()))
        except Exception as e:
            print("■■■■■■■ decodeError")

# 判断后缀
def suffix_judge(path):
    m = p.findall(path)
    if m:
        tp = m[0]
        if tp == "lua":
            return True
    else:
        return False
