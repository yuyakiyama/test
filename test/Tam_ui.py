#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import re
import sys
#要インストール
import pandas as pd
import numpy as np
import wx

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

def tam(event):
    x = text_1.GetValue()
    y = text_2.GetValue()

    A = adress_manager_v2(x,"",master)
    B = adress_manager_v2(y,"",master)

    dis = distance_manager_v2(A[0],A[1],B[0],B[1])
    text_3.SetValue("２点間の距離は"+str(round(dis/1000, 3))+"kmです。")

#def main():
master = pd.read_csv("./data/KEN_ALL.csv", encoding="shift-jis", header=None, dtype=str)

application = wx.App()
frame = wx.Frame(None, wx.ID_ANY, '距離計算器', size=(300, 150))

panel = wx.Panel(frame, wx.ID_ANY)
panel.SetBackgroundColour('#AFAFAF')

text_1 = wx.TextCtrl(panel, wx.ID_ANY)
text_2 = wx.TextCtrl(panel, wx.ID_ANY)
text_3 = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_MULTILINE)
text_3.Disable()
button_1 = wx.Button(panel, wx.ID_ANY, '計算！')

button_1.Bind(wx.EVT_BUTTON, tam)

layout = wx.BoxSizer(wx.VERTICAL)
layout.Add(text_1, flag=wx.GROW)
layout.Add(text_2, flag=wx.GROW)
layout.Add(button_1, flag=wx.GROW)
layout.Add(text_3, flag=wx.GROW)

panel.SetSizer(layout)

frame.Show()
application.MainLoop()


# if __name__ == "__main__":
#     main()
