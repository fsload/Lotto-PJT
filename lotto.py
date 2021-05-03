import gc
import itertools
import os
import random
import sys
import threading
import time
from itertools import combinations, product

TOTAL_LOTTO_INDICES = 6
MAX_LOTTO_NUM = 45

# 2중 Dictionary (a.k.a "map")
# 첫번째 Dictionary = Key : 자리수 : int - Value : 두번째 Dictionary : {}, dict()
# 두번째 Dictionary = Key : 자리수에 해당하는 값 : int - Value : 특정 자리수에 특정 값이 들어가있는 모든 조합


class IdxToValueToCombs:
    def __init__(self):
        self.map = {}
        for i in range(TOTAL_LOTTO_INDICES):
            self.map[i+1] = {}

    # @idx : 자리수
    # @idx_value : 자리수에 해당하는 값
    # @combination : 완성된 로또 번호 조합
    def push(self, idx, idx_value, combination):
        if idx_value not in self.map[idx]:
            self.map[idx][idx_value] = set()

        self.map[idx][idx_value].add(tuple(combination))

    def getCombinations(self, idx, idx_value):
        if idx not in self.map :
            return set()
        
        else :
            if idx_value not in self.map[idx] :
                return set()

            return self.map[idx][idx_value]


def init() :

    global total_combs
    global isInitiating
    global cur_lotto_combs
    global lock

    # 로또 조합 만들기 전 로딩 중 프린트 시작
    printingInitTask = threading.Thread(
        target = printInit,
        args = (lock, )
    )
    printingInitTask.start()

    # 로또 조합 만들기
    create_lotto_combinations(1, 0, [], total_combs)

    cur_lotto_combs = total_combs

    # 로또 조합 만든 후 프린트 종료
    isInitiating = False

    lock.acquire()


def printInit(lock):
    global isInitiating
    global spinner

    print("=== 로또 번호 뽑기 프로그램 ===")
    print("리소스 준비중입니다. 다소 시간이 걸릴 수 있습니다", end='', flush=True)

    periodCnt = 0
    while isInitiating:
        time.sleep(1)

        if periodCnt < 10 :
            print(".", end=' ', flush=True)
            periodCnt+= 1

        else :
            print(next(spinner), end='', flush = True)
            print('\b', end='', flush = True)

    print('', flush=True)
    lock.release()


def printLoading(preLoadingText, postLoadingText, lock) :

    global isLoading
    isLoading = True

    print(preLoadingText, flush = True)

    print("잠시만 기다려주세요.", end='', flush = True)

    while isLoading :
        time.sleep(1)
        print(".", end=" ", flush=True)

    print('', flush = True)
    print(postLoadingText, flush = True)

    lock.release()


def create_lotto_combinations(now, before, cur_comb, total_combs):

    if now - 1 == TOTAL_LOTTO_INDICES:
        global idxToValueToCombs

        for idx in range(len(cur_comb)):
            idx_value = cur_comb[idx]
            idxToValueToCombs.push(idx+1, idx_value, cur_comb)

        total_combs.add(tuple(cur_comb))
        return

    for i in range(before + 1, now + 25):
        create_lotto_combinations(now + 1, i, cur_comb + [i], total_combs)


def rand():
        rand_list = []
        rand_num = random.randint(1, MAX_LOTTO_NUM + 1)

        print("랜덤한 6 수 출력")
        for i in range(TOTAL_LOTTO_INDICES):
                while rand_num in rand_list:
                        rand_num = random.randint(1, MAX_LOTTO_NUM + 1)
                rand_list.append(rand_num)
        rand_list.sort()
        print(rand_list)


def exclude(lotto_num_candidates):

    global exclude_nums
    global fixedPosToIncludeNum
    cur_exclude_nums = []

    while True :
        try:
            input_del = int(input("제외할 번호를 입력해 주세요 : <완료/중단 : -1> "))
        except ValueError:
            print("숫자를 입력해 주세요.")
            exclude(lotto_num_candidates)
        if input_del > 45 or input_del < -1:
            print(input_del,"은 범위 밖 숫자입니다.")

        elif input_del == -1:
            break
        
        else:
            if input_del in fixedPosToIncludeNum.keys() :
                print("이미 고정된 숫자는 제외하실 수 없습니다.")
                print("(고정된 숫자를 제외하고 싶은 경우 조건을 초기화해야 합니다)")

            else :
                if input_del in cur_exclude_nums :
                    print("이미 추가된 숫자입니다")

                else :
                    try:
                        cur_exclude_nums.append(input_del)
                    except ValueError:
                        print(input_del, '은 범위 밖 숫자 입니다.')

    if len(cur_exclude_nums) == 0 or (len(cur_exclude_nums) == 1 and cur_exclude_nums == -1):
        print("제외할 숫자가 없습니다")
        return

    while True:
        shouldApply = input(
            "제외할 숫자는 "+ str(cur_exclude_nums) + "입니다. 적용하시겠습니까? (Y/N) "
        )

        if shouldApply == "Y":
            break

        elif shouldApply == 'N' :
            print("숫자 제외 취소")
            return

        print("Y/N 만 가능합니다")
    
    cur_exclude_nums.sort()

    combs_to_exclude = None
    global cur_lotto_combs
    global idxToValueToCombs
    global lock

    loadingThread = threading.Thread(
        target = printLoading,
        args = (
            "번호 제외 조건 적용 중입니다",
            "번호 제외 조건 적용 완료",
            lock
        )
    )
    loadingThread.start()

    for eachPosition in range(TOTAL_LOTTO_INDICES):
        for exclude_num in cur_exclude_nums :
            curCombination = idxToValueToCombs.getCombinations(
                eachPosition + 1,
                exclude_num
            )
            if combs_to_exclude == None :
                combs_to_exclude = curCombination

            else :
                # 제외시킬 번호가 들어간 조합들을 전부 찾는다
                combs_to_exclude = combs_to_exclude | curCombination

    exclude_nums = exclude_nums | set(cur_exclude_nums)
    
    # 로딩 프린트 종료
    global isLoading
    isLoading = False

    lock.acquire()

    # 현재까지의 조합에다, 제외시킬 번호가 들어간 조합을 차집합
    return cur_lotto_combs - combs_to_exclude 


# 특정 위치에 특정 값이 존재하는 모든 조합
# 각 자리수별로 가능한 값의 범위 검사 필요!!
#
def include_specific(lotto_num_candidates):

    global fixedPosToIncludeNum
    curFixedPosToIncludeNum = {}
    isInputFinished = False

    # 정해진 위치에 숫자를 고정 후 가능한 조합 구하기
    while True :

        while True :
            try:
                input_pos = int(input("숫자를 고정시키고 싶은 위치를 입력하세요 (1 ~ 6) <입력 중단 : -1>: "))
            except ValueError:
                print("숫자를 입력해 주세요.")
                include_specific(lotto_num_candidates)
            if input_pos > 0 and input_pos < 7 :
                if input_pos in fixedPosToIncludeNum :
                    print("해당 위치에 이미 고정된 숫자가 있습니다 : ", fixedPosToIncludeNum[input_pos])
                    print("(새로 고정을 하고 싶을 경우 조건 초기화를 해야합니다)")
                else :
                    break

            elif input_pos == -1 :
                isInputFinished = True
                break

            else :
                print("올바르지 않은 입력입니다. 1 ~ 6 까지의 정수만 입력받을 수 있습니다.")

        if isInputFinished :
            break
        # Exception Handling

        while True :
            input_num = int(input(
                str(input_pos) + "번째 자리에 고정시킬 숫자를 입력하세요 (1 ~ 45) <입력 중단 : -1>: "
            ))

            if 0 < input_num and input_num < 46 :
                break

            elif input_num == -1 :
                isInputFinished = True
                break

            else :
                print("올바르지 않은 입력입니다. 1 ~ 45 까지의 정수만 입력받을 수 있습니다.")

        
        if isInputFinished :
            break

        # Exception Handling

        if input_pos in fixedPosToIncludeNum :
            if fixedPosToIncludeNum[input_pos] != input_num :
                curFixedPosToIncludeNum[input_pos] = input_num
        else :
            curFixedPosToIncludeNum[input_pos] = input_num


        while True :
            cmd = input("추가로 숫자를 고정하시겠습니까? (Y/N) : ")
            if cmd == 'N':
                isInputFinished = True
                break

            elif cmd == 'Y' :
                break

            else :
                print("Y/N 만 가능합니다")

        if isInputFinished :
            break


    global idxToValueToCombs
    global cur_lotto_combs
    global lock

    loadingThread = threading.Thread(
        target = printLoading,
        args = (
            "번호 고정 조건 적용 중입니다",
            "번호 고정 조건 적용 완료",
            lock
        )
    )
    loadingThread.start()

    final_combinations = None

    for eachFixedPos in curFixedPosToIncludeNum.keys() :

        fixedValue = curFixedPosToIncludeNum[eachFixedPos]

        curCombination = idxToValueToCombs.getCombinations(
            eachFixedPos,
            fixedValue
        )

        if final_combinations == None :
           final_combinations = curCombination

        else :
            final_combinations = final_combinations & curCombination


    # 현재까지 적용된 (기존) 로또 번호 조합들과 교집합
    try:
        final_combinations = final_combinations & cur_lotto_combs
    except TypeError:
        print("고정할 값이 없습니다.")
    fixedPosToIncludeNum.update(curFixedPosToIncludeNum)

    # 로딩 프린트 종료
    global isLoading
    isLoading = False

    lock.acquire()

    return final_combinations

def exclude_set(lotto_num_candidates):
    global exclude_sets_num
    global fixedPosToIncludeNum
    global printDelSet
    cur_exclude_sets = []

    while True:
        try:
            input_set = int(input("제외할 조합을 입력해 주세요 : <완료/중단 : -1> "))
        except ValueError:
            print("숫자를 입력해 주세요.")
            exclude_set(lotto_num_candidates)
        if input_set == -1:
            break
            
        else:
            if input_set > 45 or input_set < -1 :
                print("범위 밖 숫자입니다.")

            else :
                if input_set in cur_exclude_sets :
                    print("이미 추가된 숫자입니다")
                    break
                else :
                    try:
                        cur_exclude_sets.append(input_set)

                    except ValueError:
                        print(input_set, '은 범위 밖 숫자 입니다.')
    
    if len(cur_exclude_sets) == 0:
        print("제외할 조합이 없습니다")
        return
        
    cur_exclude_sets.sort()

    while True:
        shouldApply = input("제외할 조합은 "+ str(cur_exclude_sets) + "입니다. 적용하시겠습니까? (Y/N) ")
        
        if shouldApply == "Y":
            break

        elif shouldApply == 'N' :
            print("숫자 제외 취소")
            return

        print("Y/N 만 가능합니다")

    if len(printDelSet) > 140:
        print("현재 적용 조건 목록이 최대에 도달했습니다. 목록을 초기화 합니다.")
        del printDelSet[:]

    printDelSet.append(cur_exclude_sets)
    combs_to_exclude = None
    global cur_lotto_combs
    global idxToValueToCombs
    global lock

    loadingThread = threading.Thread(
        target = printLoading,
        args = (
            "조합 제외 조건 적용 중입니다",
            "조합 제외 조건 적용 완료",
            lock
        )
    )
    loadingThread.start()


    for eachPosition in range(TOTAL_LOTTO_INDICES):
        
        for exclude_set_num in cur_exclude_sets :
            
            curCombination = idxToValueToCombs.getCombinations(
                eachPosition + 1,
                exclude_set_num
            )
            
            if combs_to_exclude == None :
                combs_to_exclude = curCombination
            else :
                combs_to_exclude = combs_to_exclude | curCombination
    exclude_sets_num = exclude_sets_num | set(cur_exclude_sets)

    combs_to_exclude = list(combs_to_exclude)
    setTodel = []
    chk = 0
    

    for perList in combs_to_exclude:
        chk = 0

        for number in cur_exclude_sets:
            if number in perList:
                chk = chk + 1
                if chk == len(cur_exclude_sets):
                    setTodel.append(perList)
                    break
                

    combs_to_exclude = set(setTodel)
                    

    # 로딩 프린트 종료
    global isLoading
    isLoading = False

    lock.acquire()
    # 현재까지의 조합에다, 제외시킬 번호가 들어간 조합을 차집합
    return cur_lotto_combs - combs_to_exclude 



def create_text_file(cur_lotto_combs):

    result = []

    cur_time = time.strftime(
       '%y-%m-%d-%H-%M-%S', 
       time.localtime(time.time())
    )

    fileName = cur_time + '_lotto.txt'

    global lock

    loadingThread = threading.Thread(
        target = printLoading,
        args = (
            "조건에 맞는 로또 번호 파일 생성 시작 (파일명 : " + fileName + " )",
            "로또 번호 파일 생성 완료",
            lock
        )
    )
    loadingThread.start()

    cur_lotto_combs_list = list(cur_lotto_combs)
    cur_lotto_combs_list.sort()

    for comb in cur_lotto_combs_list:
        result.append(str(comb) + '\n')

    with open (fileName, 'x', newline = None) as f:
        f.writelines(result)

    # 로딩 프린트 완료
    global isLoading
    isLoading = False

    print(fileName, '가 생성되었습니다.', flush=True)

    lock.acquire()

# 특정 위치에 특정 값이 존재하지 않는 모든 조합
# 각 자리수별로 가능한 값의 범위 검사 필요!!
#
def exclude_specific(lotto_num_candidates):

    global fixedPosToExcludeNum
    global exclude_nums
    curFixedPosToExcludeNum = {}
    isInputFinished = False

    # 정해진 위치에 숫자를 고정 후 가능한 조합 구하기
    while True :

        while True :
            try:
                input_num = int(input("제외시키고 싶은 숫자를 입력하세요 (1 ~ 45) <입력 중단 : -1>: "))
            except ValueError:
                print("숫자를 입력해 주세요")
                exclude_specific(lotto_num_candidates)
            if 0 < input_num and input_num < 46 :
                if input_num in exclude_nums :
                    print("이미 전체에서 제외된 숫자입니다")
                else :
                    break

            elif input_num == -1 :
                isInputFinished = True
                break

            else :
                print("올바르지 않은 입력입니다. 1 ~ 45 까지의 정수만 입력받을 수 있습니다.")

        
        if isInputFinished :
            break

        while True :
            input_pos = int(
                input(
                    str(input_num) + "을 제외시킬 위치를 입력하세요 (1 ~ 6) <입력 중단 : -1>: "
                    )
                )

            if input_pos > 0 and input_pos < 7 :
                break

            elif input_pos == -1 :
                isInputFinished = True
                break

            else :
                print("올바르지 않은 입력입니다. 1 ~ 6 까지의 정수만 입력받을 수 있습니다.")

        if isInputFinished :
            break

        # Exception Handling
        if input_pos in fixedPosToExcludeNum :
            if fixedPosToExcludeNum[input_pos] != input_num :
                curFixedPosToExcludeNum[input_pos] = input_num
        else :
            curFixedPosToExcludeNum[input_pos] = input_num

        while True :
            cmd = input("추가로 숫자를 제외하시겠습니까? (Y/N) : ")
            if cmd == 'N':
                isInputFinished = True
                break

            elif cmd == 'Y' :
                break

            else :
                print("Y/N 만 가능합니다")

        if isInputFinished :
            break

    global idxToValueToCombs
    global total_combs
    global isLoading
    global cur_lotto_combs
    global lock

    loadingThread = threading.Thread(
        target = printLoading,
        args = (
            "제외 조건 적용 중입니다",
            "제외 조건 적용 완료",
            lock
        )
    )
    loadingThread.start()

    final_combinations = set()

    for eachFixedPos in curFixedPosToExcludeNum.keys() :

        fixedValue = curFixedPosToExcludeNum[eachFixedPos]

        curCombination = idxToValueToCombs.getCombinations(
            eachFixedPos,
            fixedValue
        )
        if len(final_combinations) == 0 :
            final_combinations = curCombination
        else :
            # 제외시킬 번호 교집합
            final_combinations =  final_combinations & curCombination
    try:
        final_combinations = cur_lotto_combs - final_combinations
    except TypeError:
        print("제외시킬 숫자가 없습니다.")
        return final_combinations
    fixedPosToExcludeNum.update(curFixedPosToExcludeNum)

    # 연산 종료 후 프린트 종료
    global isLoading
    isLoading = False

    lock.acquire()

    return final_combinations


# ========== Global Area ====================
isInitiating = True
isLoading = False

fixedPosToExcludeNum = {}
fixedPosToIncludeNum = {}

idxToValueToCombs = IdxToValueToCombs()

lotto_num_candidates = []
for i in range(MAX_LOTTO_NUM):
    lotto_num_candidates.append(i+1)
   
# 모든 조합 만들기
printDelSet = []
total_combs = set()
cur_lotto_combs = set()
exclude_nums = set()
exclude_sets_num = set()
lock = threading.Semaphore(0)

spinner = itertools.cycle(['-', '/', '|', '\\'])

init()

# ===========================================


def main() :

    global lotto_num_candidates
    global cur_lotto_combs
    global fixedPosToExcludeNum
    global fixedPosToIncludeNum
    global exclude_nums
    global exclude_sets_num
    global printDelSet



    while True:
    # select mode
        print('')
        print ("==== 지원하는 모드 =====================")
        print ("[조건] 제외 시킬 번호 추가 : 1")
        print ("[조건] 제외 시킬 번호와 위치 추가 : 2")
        print ("[조건] 번호와 위치를 고정 추가 : 3")
        print ("[조건] 제외 시킬 조합 추가 : 4")
        print ("[파일] 현재 적용된 조건 텍스트 파일로 생성 : 5")
        print ("[랜덤] 무작위 숫자 출력 : 6")
        print ("[조건] 현재 적용 조건 목록 출력 : 7")
        print ("[조건] 조건 초기화 : 8")
        print ("<권장> 실행 종료 : 9")
        print ("=====================================")
        try:
            command = int(input("원하는 모드를 입력하세요 : "))
        except Exception:
            print("잘못된 명령입니다. ")
            main()
    

        if command < 0 or command > 9:
            print ("잘못된 명령입니다. ")
        else :
            if command == 1:
                cur_lotto_combs = exclude(lotto_num_candidates)

            elif command == 2:
                cur_lotto_combs = exclude_specific(lotto_num_candidates)

            elif command == 3:
                cur_lotto_combs = include_specific(lotto_num_candidates)

            elif command == 4:
                cur_lotto_combs = exclude_set(lotto_num_candidates)

            elif command == 5:
                create_text_file(cur_lotto_combs)

            elif command == 6:
                rand()

            elif command == 7 :
                print(" 1. 현재 제외된 숫자 목록")
                print("   ->  "+str(exclude_nums))
                print(" 2. 특정 위치에서 제외된 숫자 목록")
                
                for fixedPos in fixedPosToExcludeNum.keys() :
                    print("   -> ", end='')
                    print(" 위치 :", fixedPos, "/ 숫자 :", fixedPosToExcludeNum[fixedPos])

                print(" 3. 특정 위치에 고정된 숫자 목록")

                for fixedPos in fixedPosToIncludeNum.keys() :
                    print("   -> ", end='')
                    print(" 위치 :", fixedPos, "/ 숫자 :", fixedPosToIncludeNum[fixedPos])
                print(" 4. 현재 제외된 조합")
                print("   ->  "+str(printDelSet))
            elif command == 8:
        
                del cur_lotto_combs
                del fixedPosToExcludeNum
                del fixedPosToIncludeNum
                del exclude_nums
                del exclude_sets_num
                del printDelSet

                exclude_sets_num = set()
                exclude_nums = set()
                fixedPosToExcludeNum = {}
                fixedPosToIncludeNum = {}
                cur_lotto_combs = total_combs
                printDelSet = []

                print("조건 초기화 완료!")

            elif command == 9:
                print("프로그램 종료 중입니다")
                gc.collect()
                sys.exit()
        #except Exception:
        #    print("잘못된 입력 입니다.")
        #    main()
                

main()
