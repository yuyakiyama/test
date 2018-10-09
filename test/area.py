#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pandas as pd
from pygeocoder import Geocoder
#scale=Geocoder.geocode("1570061")
#scale.coordinates
import folium
import time
import re

def num2kanzi(fullpass, ex):
    to_list = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    word = "丁目"
    subpass = fullpass[len(ex):]#郵便番号で判明する部分を省く
    if subpass.find(word)== -1:#～丁目書きでない
        if subpass.find("-")== -1:#異常住所
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
        return fullpass

def adress_manager_v2(num, fullpass,master):
    # 入力された郵便番号の対応する情報抽出
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
    point=[]
    if adress.iloc[0, 2] == "以下に掲載がない場合":  # 例外処理
        point.append(town["緯度"].astype(float).mean())
        point.append(town["経度"].astype(float).mean())
    elif len(fullpass)==0: # 住所データなし
        temp = list(map(lambda x: adress.iloc[0, 2] in x, town['大字町丁目名']))
        town = town[temp]
        point = list(town[["緯度", "経度"]].astype(float).mean())
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
            try:
                point.append(town["緯度"].astype(float).mean())
                point.append(town["経度"].astype(float).mean())
            except:
                print("エラー：",adress[0],adress[1],adress[2])
                return [0,0,"グリニッジ"]
    ex = adress.iloc[0, 0] + adress.iloc[0, 1] + adress.iloc[0, 2]
    return [point[0],point[1],ex]

args = sys.argv

master = pd.read_csv("./data/KEN_ALL.csv", encoding="shift-jis", header=None, dtype=str)

temp = pd.read_csv("./data/shop_all.csv", encoding="cp932", dtype=str, engine="python")
#print(master)
temp["郵便番号"] = temp["郵便番号"].replace('(.*)-(.*)', r'\1\2', regex=True)

m = folium.Map(location=[35, 135], zoom_start=9)
for adress,live in zip(temp["郵便番号"],temp["住所"]):
    point = adress_manager_v2(adress,live,master)
    if point[0]==point[0]:
        #folium.Marker([point[0], point[1]], popup=adress, icon=folium.Icon(color='blue')).add_to(m)
        folium.Circle(
            location=[point[0], point[1]],
            radius=args[1],
            color='#3186cc',
            fill_color='#3186cc'
        ).add_to(m)
    time.sleep(0.1)
name = "map"+str(args[1])+".html"
m.save(name)
print("end")
