#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import sys
import math

args = sys.argv

# 郵便番号がすべて載っているデータ
master = pd.read_csv("./data/KEN_ALL.csv", encoding="shift-jis", header=None, dtype=str)

def adress_manager(num): #緯度経度抽出
    # 入力された郵便番号の対応する情報抽出
    adress = master[master[2] == num][[6, 7, 8]]
    if len(adress)==0:#存在しない場合
        return 0
    # 都道府県名抽出
    prefecture = adress.iloc[0, 0]
    # 各都道府県データ読み込み
    prefecture = "./data/" + prefecture + ".csv"
    pref = pd.read_csv(prefecture, encoding="cp932", dtype=str, engine="python")
    # 市区町村名で抽出
    town = pref[pref["市区町村名"] == adress.iloc[0, 1]]
    # より細かい地名を部分一致で抽出
    adress=adress.replace('(.*)[（](.*)[）]', r'\1', regex=True)
    if adress.iloc[0,2]=="以下に掲載がない場合":#例外処理
        point = list(town[["緯度", "経度"]].astype(float).mean())
    else:#通常処理
        temp = list(map(lambda x: adress.iloc[0, 2] in x, town['大字町丁目名']))
        town = town[temp]
        point = list(town[["緯度", "経度"]].astype(float).mean())
    return point

#ヒュベニの公式
def deg2rad(deg):#度数をラジアンに変換
    return(deg * (2 * math.pi) / 360)

def distance_manager_v2(lat1,lon1,lat2,lon2): #緯度経度から実距離算出
    if lat1==lat1 and lat2==lat2:#nan対処
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
    else:
        return 0

#テスト用データ作成
kenmei = args[1]
kumei = args[2]
dummy = master[master[6]==kenmei][[2,7]]
arr = np.random.randint(4, 1000, (len(dummy),1))
dummy["person"]=arr
test=dummy[dummy[7]==kumei]

#listに入った郵便番号に距離を付加
Yubin1 = args[3] #基準点
point_A = adress_manager(Yubin1)
yubin_temp = list(test[2])
dis_list = [] #距離のリスト
for i in yubin_temp:
    point_B = adress_manager(i)
    dis_list.append((i,distance_manager_v2(point_A[0],point_A[1],point_B[0],point_B[1])))
dis_list = pd.DataFrame(dis_list)
test = pd.merge(test,dis_list,left_on = 2,right_on= 0)

#距離を昇順でソート
test=test.sort_values(1)#1=distance

#総人数と郵便番号の数を算出
max_person = test["person"].sum()
max_count = test[2].count()
c8 = int(max_count*0.8)
p8 = max_person*0.8

#郵便番号の数の80%で人数算出
test8 = test[:c8]
pc8 = test8["person"].sum()

#high&lowで処理
#highからlowに転じるタイミングで終了
flag = False
while True:
    if pc8 > p8:#high
        flag = True
        pc8 -= test.iloc[c8,2]
    elif pc8 < p8:#low
        if flag:
            break
        c8 += 1
        pc8 += test.iloc[c8,2]

while True:
    if test.iloc[c8,4]!=0:
        break
    c8 += 1

#80%にできるだけ近づける
distance_length = test.iloc[c8+1,4]-test.iloc[c8,4]
distance_person = test.iloc[c8+1,2]
per_l_p = distance_length / distance_person
remain = p8 - pc8
ans = test.iloc[c8,4] + (per_l_p * remain)
ans = round(ans/1000, 3)

print("商店登録人数",max_person,"人\n")
print("登録郵便番号数",max_count,"件\n")
ans = round(float(test.iloc[c8,4])/1000, 3)
print("80%商圏は",ans,"kmです。")
