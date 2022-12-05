#!/usr/bin/python

#****************************************************************#
# ScriptName:
# ScriptDesc: Used in performance test, fio bind cpu core, default is 8 logic core / 4 physics core
# Modify Author: ScaleFlux
# Modify Date:
# Version: 1.0
#***************************************************************#

# get test env cpu num
# check if every card need test in this case can get enough core
# if True, check siblings, and bind cpu for every card
# return to shell

import argparse
import os
import math
import copy
import time

# card_bind_core = list()

def checkEnv(card_num, cpu_bind_num):
    """
    get cpu core
    check if card can get enough logic core
    """
    cpu_core = os.popen("numactl --hardware | grep cpus ").read().splitlines()
    if "command not found" in cpu_core:
        os.popen("echo y | sudo yum install numactl")
        cpu_core = os.popen("numactl --hardware | grep cpus ").read().splitlines()
    cpu_dic = {}
    for node in cpu_core:
        cpu_dic[node.split(":")[0]] = node.split(":")[-1]
    numa_num = len(cpu_dic)
    core_num = int(len(cpu_dic.get("node 0 cpus").split(' '))) - 1
    calcul_value = math.ceil((int(card_num)+1) / int(numa_num)) * int(cpu_bind_num)
    if int(calcul_value) <= core_num:
        print("check env ok, have enough core for card bind")
    else:
        print("not enough core num for every card bind to test, total card num is {}, total logic core num is {}".
              format(int(card_num)+1, core_num * numa_num))
        exit(0)
    return cpu_dic

def bindSiblings(cpu_dict, card_num, cpu_bind_num):
    """split cpu """
    keys = cpu_dict.keys()
    card_bind_core = list()
    numa_num = len(cpu_dict)
    need_bind_num = int((int(card_num)+1) / numa_num)
    count_num = 1
    for key in keys:
        core_list = cpu_dict[key].split(' ')[1:]
        if count_num == numa_num:
            card_bind_core = checkSiblings(card_bind_core, core_list, need_bind_num, cpu_bind_num)
        else:
            card_bind_core = checkSiblings(card_bind_core, core_list, (int(card_num) + 1 - need_bind_num) , cpu_bind_num)
        count_num += 1
    return card_bind_core


def checkSiblings(card_bind_core, core_list, card_num, cpu_bind_num):
    card_bind = list()
    count = 0
    # card_bind_core = list()
    copy_core_list = copy.deepcopy(core_list)
    for core in core_list:
        siblings = os.popen("cat /sys/devices/system/cpu/cpu{}/topology/thread_siblings_list".format(core)).read()
        for sib in list(siblings.split(',')):
            if sib.rstrip() not in copy_core_list:
                continue
            else:
                card_bind.append(str(int(sib.rstrip())))
                if len(card_bind) == cpu_bind_num:
                    card_bind_core.append(card_bind)
                    count += 1
                    card_bind = list()
                copy_core_list.remove(str(int(sib.rstrip())))
        if count == card_num:
            break
    return card_bind_core


def getParameter():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=str,
                        help="please card num which need test in case")
    parser.add_argument("-c", type=int, default=8,
                        help="please input cpu logic core which you need bind")


    args = parser.parse_args()
    return args.n, args.c


if __name__ == "__main__":

    n, c = getParameter()
    if n is None:
        raise Exception("please input card num")
    if n == '1':
        print("No need to bind-cpu-core when only testing single ssd")
        exit(0)
    cpu_dict = checkEnv(n, c)
    card_bind_core = bindSiblings(cpu_dict, n, c)
    card_list = dict()

    os.popen("rm -f card_bind_core.log")
    for i in range(int(n) + 1):
        card_bind_str = ','.join(card_bind_core[i])
        os.popen("echo -e nvme{}n1 {} >> card_bind_core.log".format(i, card_bind_str))
        time.sleep(1)
        card_list["nvme{}n1".format(i)] = card_bind_core[i]
    print(card_list)

    # os.popen("echo -e {} > card_bind_core.log".format(card_list))

    # if len(card_list) == len(card_bind_core):
    #     zipped = list(zip(card_list, card_bind_core))
    #     print(zipped)
    # else:
    #     print("There are some wrong, pls check, card num is {}, card_bind_core is {}".format(int(n)+1, card_bind_core))


