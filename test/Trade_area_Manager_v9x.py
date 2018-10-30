#!/usr/bin/env python
# -*- coding: utf-8 -*-

#226,270,272行目は環境によって書き換えてください

import math
import re
import sys
import os
#要インストール
import pandas as pd
import numpy as np
import wx
import folium
from selenium import webdriver
#ブラウザdriverとってきてPATH通す(ユーザ変数)

#保存のため
global client_count
global cnt
global cnt2
global m

#UI制御用のグローバル変数群
application = wx.App()
frame = wx.Frame(None, wx.ID_ANY, '商圏探索機', size=(300, 400))

panel = wx.Panel(frame, wx.ID_ANY,size=(300,400))
panel.SetBackgroundColour('#AFAFAF')

text_1 = wx.TextCtrl(panel, wx.ID_ANY,"./data/yubin.csv")
text_2 = wx.TextCtrl(panel, wx.ID_ANY,"./data/test.csv")
text_3 = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_MULTILINE)
text_4 = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_MULTILINE)
button_2 = wx.Button(panel, wx.ID_ANY, 'csv保存！')
#button_3 = wx.Button(panel, wx.ID_ANY, '地図表示！')
button_4 = wx.Button(panel, wx.ID_ANY, 'スクショ保存！')
button_5 = wx.Button(panel, wx.ID_ANY, '地図保存！(html)')
text_1.SetMaxLength(7) #郵便番号のみ受けつけたいので７桁縛り

#距離計算関数系
def deg2rad(deg):#度数をラジアンに変換
    return(deg * (2 * math.pi) / 360)

def distance_manager_v2(lat1,lon1,lat2,lon2):#ヒュベニの公式
    lat1 = float(lat1)
    lon1 = float(lon1)
    lat2 = float(lat2)
    lon2 = float(lon2) #念のためのfloat化
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
    #漢数字のリスト
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
        #郵便番号でわかる住所を連結
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
    temp4 = [] #保存用リスト群
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
    test=client_count.sort_values("距離")#1=distance
    test=test.drop_duplicates()
    #総人数と郵便番号の数を算出
    max_person = test["人数"].sum()
    max_count = len(test)
    c8 = int(max_count*per)
    p8 = int(max_person*per)

    #郵便番号の数の80%で人数算出
    test8 = test[:c8]
    pc8 = test8["人数"].sum()

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

def reader(yubin):#単体複数対応機構
    pattern = r"[a-xA-Z0-9_](.csv)"
    chack = re.search(pattern , yubin)
    shop = []
    if chack:
        temp= pd.read_csv(yubin, encoding="cp932", dtype=str)
        shop = list(temp["郵便番号"])
    else:
        shop.append(yubin)
    return shop

def tam(event):#主計算部(ほぼすべての計算を受け持つ)
    master = pd.read_csv("./data/KEN_ALL.csv", encoding="shift-jis", header=None, dtype=str)
    global client_count
    global m
    x = text_1.GetValue()#店舗
    y = text_2.GetValue()#顧客
    text_3.SetValue("")#最初は空欄
    text_4.SetValue("")
    client= pd.read_csv(y, encoding="cp932", dtype=str)
    add = reader(x)#内包された郵便番号のリストを返す
    title = "" #出力用
    text = ""
    flag = True
    for yu in add:
        shop_adress = adress_manager_v2(yu,"",master)#特殊仕様
        client_count = client_manager(client,master,shop_adress)
        client_count.drop("ido", axis=1,inplace=True)
        client_count.drop("keido", axis=1,inplace=True)
        client_count.rename(columns={"adress" : "人数"}, inplace=True)
        client_count.rename(columns={"distance" : "距離"}, inplace=True)#出力用の整形
        ans = cal_ta(client_count)
        c_ans = client_count[client_count["距離"]<=ans]
        cc = client_count["人数"].sum()
        amount=c_ans["人数"].sum()
        title += str(yu)+"の80%商圏は"+str(round(ans/1000, 3))+'kmです。\n'
        text += str(yu)+"\n郵便番号\t商品\t\t人数\n"
        for i in range(len(c_ans)):
            text += str(c_ans.iloc[i,0])+"\t"+str(c_ans.iloc[i,2])+"\t"+str(c_ans.iloc[i,3])+"人\n"
        text += "\n"
        button_2.Enable()
        button_5.Enable()
        meter = round(ans/1000, 3)
        if flag:
            m = folium.Map(location=[shop_adress[0], shop_adress[1]], zoom_start=12)
            flag = False
        folium.Marker([shop_adress[0], shop_adress[1]], popup=str(yu)+"\n"+str(meter)+"km", icon=folium.Icon(color='blue')).add_to(m)
        folium.Circle(
            location=[shop_adress[0], shop_adress[1]],
            radius=(meter*1000),
            color='#3186cc',
            fill_color='#3186cc'
        ).add_to(m)
    text_3.SetValue(title)
    text_4.SetValue(text)
    m.save("map.html")
    browser = webdriver.Ie(r"C:\Users\yuya_kiyama\python\IEDriverServer.exe")
    browser.set_window_size(500,600)
    browser.get('file:///C:/Users/yuya_kiyama/python/Yubin/pg/map.html')

def save(event):
    global cnt
    df = client_count
    df.to_csv("list"+str(cnt)+".csv",index=False,encoding="cp932")
    cnt += 1
    button_2.Disable()

def savemap(event):
    global cnt
    global cnt2
    if cnt2 != cnt-1:
        cnt2 = cnt-1
    m.save("map"+str(cnt2)+".html")
    #button_3.Disable()

def main():
    global cnt
    global cnt2
    cnt = 1
    cnt2 = 1
    button_1 = wx.Button(panel, wx.ID_ANY, '計算！')

    button_1.Bind(wx.EVT_BUTTON, tam)
    button_2.Bind(wx.EVT_BUTTON, save)
    button_5.Bind(wx.EVT_BUTTON, savemap)

    layout = wx.BoxSizer(wx.VERTICAL)
    layout.Add(text_1, flag=wx.GROW)
    layout.Add(text_2, flag=wx.GROW)
    layout.Add(button_1, flag=wx.GROW)
    layout.Add(button_2, flag=wx.GROW)
    layout.Add(button_5, flag=wx.GROW)
    layout.Add(text_3, flag=wx.GROW)
    layout.Add(text_4, flag=wx.GROW,proportion=1)
    button_2.Disable()
    button_5.Disable()
    panel.SetSizer(layout)
    frame.SetSizer(layout)

    frame.Show()
    application.MainLoop()


if __name__ == "__main__":
    main()
