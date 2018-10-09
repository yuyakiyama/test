#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import re
import sys
#要インストール
import pandas as pd
import numpy as np

#距離計算関数系
def deg2rad(deg):#度数をラジアンに変換
    return(deg * (2 * math.pi) / 360)

def distance_manager_v2(lat1,lon1,lat2,lon2):#ヒュベニの公式
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2)
    if lat1==lat1 and lat2==lat2:#NaN対策
        a = 6378137.000
        b = 6356752.314140
        e = math.sqrt((a**2 - b**2) / a**2)
        e2 = e**2
        mnum = a * (1 - e2)

        my = deg2rad((lat1+lat2) / 2.0)
        dy = deg2rad(lat1-lat2)
        dx = deg2rad(lon1-lon2)
        sin = math.sin(my)
        w = math.sqrt(1.0-e2 * sin * sin)
        m = mnum / (w * w * w)
        n = a/w
        dym = dy*m
        dxncos = dx*n*math.cos(my)
        distance = math.sqrt(dym**2 + dxncos**2)
        distance = round(distance, 2)
        return distance
    else:#入力がNaNの時
        return 0

def num2kanzi(fullpass, ex):#数字を漢数字に変換
    to_list = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    word = "丁目"
    subpass = fullpass[len(ex):]#郵便番号で判明する部分を省く
    if subpass.find(word)== -1:#～丁目書きでない
        if subpass.find("-")== -1:#異常住所(丁目が存在しない場合も含む)
            return ex
        else:#-(ハイフン)書き
            subpass = subpass[:subpass.find("-")]
    else:#～丁目書き
        subpass = subpass[:subpass.find(word)]
    if not subpass[-1] in to_list:#漢数字判定と全角半角修正
        try:
            subpass = str(int(subpass))
        except:
            return fullpass
    tester = re.findall('[0-9]', subpass)#桁数分解(漢数字なら返り値なし)
    if len(tester) == 2:#2桁
        if int(tester[0]) != 1:#20～
            ans = to_list[int(tester[0])] + "十" + to_list[int(tester[1])]
        else:#10～19
            ans = "十" + to_list[int(tester[1])]
        return ex + ans + word
    elif len(tester) == 1:#1桁
        ans = to_list[int(tester[0])]
        return ex + ans + word
    elif len(subpass)!=0:#漢数字
        return ex + subpass + word
    else:#異常住所
        return ex

def ido_keido(ido,keido):#緯度経度の平均値を返す
    return ido.astype(float).mean(),keido.astype(float).mean()

def adress_manager_v2(num, fullpass,master):#郵便番号から住所を検索
    # 入力された郵便番号の対応する情報抽出
    if re.match(r'[0-9]+-[0-9]+', num):
        num = num[0:3]+num[4:8]#ハイフン対応
    adress = master[master[2] == num][[6, 7, 8]]
    if len(adress) == 0:  # 存在しない場合
        return [0,0,"グリニッジ"]
    adress = adress.replace('(.*)[（](.*)[）]', r'\1', regex=True)  # ()対応
    # 都道府県名抽出
    prefecture = adress.iloc[0, 0]
    # 各都道府県データ読み込み
    prefecture = "./data/" + prefecture + ".csv"
    try:
        pref = pd.read_csv(prefecture, encoding="cp932", dtype=str, engine="python")
    except:  # 指定都道府県データがないor読み込めない
        return [0,0,"グリニッジ"]
    # 市区町村名で抽出
    town = pref[pref["市区町村名"] == adress.iloc[0, 1]]
    # より細かい地名を抽出
    point = []
    if adress.iloc[0, 2] == "以下に掲載がない場合":  # 例外処理
        point = ido_keido(town["緯度"],town["経度"])
    elif len(fullpass)==0: # 住所データなし
        temp = list(map(lambda x: adress.iloc[0, 2] in x, town['大字町丁目名']))
        town = town[temp]
        point = ido_keido(town["緯度"],town["経度"])
    else:  # 通常処理
        ex = adress.iloc[0, 0] + adress.iloc[0, 1] + adress.iloc[0, 2]
        text = num2kanzi(fullpass, ex)  # 数字表記を漢数字表記に変換
        # ～区以下の住所抽出
        adress.iloc[0, 2] = text[len(adress.iloc[0, 0]+adress.iloc[0, 1]):]
        town2 = town[town['大字町丁目名'] == adress.iloc[0,2]]
        try:
            point.append(float(town2.iloc[0,6]))
            point.append(float(town2.iloc[0,7]))
        except:
            point = ido_keido(town["緯度"],town["経度"])
    ex = adress.iloc[0, 0] + adress.iloc[0, 1] + adress.iloc[0, 2]
    return [point[0],point[1],ex]

def client_manager(client,master,shop_adress):#返り値は詳細住所とその人数
    post_adress=client[["郵便番号","商品"]].copy()#cal_ta内の人数カウントの位置がずれるので注意
    post_adress["郵便番号"] = client["郵便番号"].replace('(.*)-(.*)', r'\1\2', regex=True)
    temp = []
    temp2 = []
    temp3 = []
    temp4 = []
    for i in range(int(len(post_adress))):
        post_temp = adress_manager_v2(post_adress.iloc[i,0],"",master)#特殊仕様
        distance = distance_manager_v2(shop_adress[0],shop_adress[1],post_temp[0],post_temp[1])
        temp.append(post_temp[0])
        temp2.append(post_temp[1])
        temp3.append(post_temp[2])
        temp4.append(distance)
    post_adress["ido"]=temp
    post_adress["keido"]=temp2
    post_adress["adress"]=temp3
    post_adress["distance"]=temp4
    client_count=post_adress.groupby(["郵便番号","distance","商品"]).count().reset_index()
    return client_count

def cal_ta(client_count):#商圏計算
    #距離を昇順でソート
    per = 0.8
    print(client_count)
    test=client_count.sort_values("distance")#1=distance
    test=test.drop_duplicates()
    #総人数と郵便番号の数を算出
    max_person = test["adress"].sum()
    max_count = len(test)
    c8 = int(max_count*per)
    p8 = int(max_person*per)

    #郵便番号の数の80%で人数算出
    test8 = test[:c8]
    pc8 = test8["adress"].sum()

    #high&lowで処理
    flag = False
    while True:
        if pc8 > p8:#high
            flag = True
            pc8 -= test.iloc[c8,3]#人数カウント
            c8 -= 1
        elif pc8 < p8:#low
            if flag:
                break
            c8 += 1
            pc8 += test.iloc[c8,3]
        else:
            break

    while True:
        if test.iloc[c8,1]==0:#距離
            c8 += 1
        elif test.iloc[c8,1]>=1000000:
            c8 -= 1
        else:
            break

    distance_length = test.iloc[c8+1,1]-test.iloc[c8,1]
    distance_person = test.iloc[c8+1,3]
    per_l_p = distance_length / distance_person
    remain = p8 - pc8
    ans = test.iloc[c8,1] + (per_l_p * remain)
    return ans

def main():
    args = sys.argv #店舗の郵便番号orそのリスト、顧客のリスト

    master = pd.read_csv("./data/KEN_ALL.csv", encoding="shift-jis", header=None, dtype=str)

    client= pd.read_csv(args[2], encoding="cp932", dtype=str)
    shop_adress = adress_manager_v2(args[1],"",master)#特殊仕様
    client_count = client_manager(client,master,shop_adress)

    ans = cal_ta(client_count)
    c_ans = client_count[client_count["distance"]<=ans]
    cc = client_count["ido"].sum()
    amount=c_ans["ido"].sum()

    print("80%商圏は",round(ans/1000, 3),'kmです。')
    #print("人数は",amount,"人で、全体の",round(amount/cc, 3)*100,"%です。")
    print(c_ans[["郵便番号","商品"]])


if __name__ == "__main__":
    main()
