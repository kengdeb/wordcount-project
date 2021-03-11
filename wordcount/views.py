from django.http import HttpResponse
from django.shortcuts import render
import operator
import os
import sys
import ntpath
import shutil
import time
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions, Chrome

def home (request):
    return HttpResponse('Hello')

def keng(request):
    return render(request,'home.html',{'hithere': 'This is me'})

def about(request):
    return render(request,'about.html')

def count(request):
    fulltext = request.GET['fulltext']

    wordlist = fulltext.split()

    wordDict = {}

    for word in wordlist:
        if word in wordDict:
            wordDict[word] +=1
        else:
            wordDict[word] = 1

    sortedWord = sorted(wordDict.items(),key = operator.itemgetter(1), reverse = True)


    return render(request,'count.html',{'fullText':fulltext, 'count': len(wordlist),'wordDict':wordDict, 'wordDictList':sortedWord})

def connectDB(db_name):
    import pyodbc
    conn=False ;error=''
    try: #Do not put a space after the Driver keyword in the connection string
        conn_str='DRIVER={ODBC Driver 17 for SQL Server};SERVER=sql-supplychain.database.windows.net;DATABASE='+db_name+';'\
                    'UID=scccadm;PWD=P@ssw0rd@1;' #'Trusted_Connection=yes;' #'autocommit=True')
        conn = pyodbc.connect(conn_str)
    except Exception as e: error=str(e)
    if not conn: print('Error, did not connect DB by pyodbc.connect(conn_str)',error)
    return conn

def sql_execute_query(db_name,query,sql_var=None,is_print_query=False): #if no paremeter, set to None
    import pandas as pd
    #---1. Set parameters for query
    if query=='' or db_name=='': return None #if sql_var={}, sql_var.values()=[]
    sql_var=None if isinstance(sql_var,dict) and not sql_var else sql_var
    params=list(sql_var.values()) if isinstance(sql_var,dict) else sql_var #sql_var.items()
    df=None
    conn=connectDB(db_name)#.connect()
    if not conn: return None
    try:
        cursor=conn.cursor()
        if params is None : rows=cursor.execute(query).fetchall()
        else: rows=cursor.execute(query,params).fetchall() #SQL Server format-->#while rows: print(rows)
        #print('yyyyyyyy Complete {}...'.format(query[:200]))
        #-------------------------------------
        columns=[column[0] for column in cursor.description] #must before move cursor
        df=pd.DataFrame.from_records(rows,columns=columns) #df=pd.read_sql(sql=query,con=conn,params=params)
        if is_print_query:
            print("------Execute query----- \n",query)
            if cursor.nextset():
                try: print('------Query -----',cursor.fetchall()[0][0])
                except Exception as e:
                    print('zzzzzzzz Error when print query',e)
                    return None
        cursor.commit() #need when update db ,ex.'delete_predo_shipment'
    except Exception as e:
        print('zzzzzzzz Error; cannot execute {} :: {}'.format(query,e))
    finally:
        cursor.close()
        conn.close()
    return df

def DasPassword(username, password):

    """ Input DAS username and Password, return driver to use in next step"""

    opts = ChromeOptions()
    opts.add_experimental_option("detach",True)
    driver = webdriver.Chrome(executable_path = ChromeDriverManager().install(),options = opts)
    driver.implicitly_wait(10)
    driver.maximize_window()

    baseURL = "http://10.224.29.107/cement/user/login"
    driver.get(baseURL)
    driver.find_element_by_id("username").send_keys(username)
    driver.find_element_by_id("password").send_keys(password)
    driver.find_elements_by_xpath("//input[@type='submit' and @value='Sign In']")[0].click()

    return driver
def DasWBInfoExtract(driver):
    """
    Extract weightbridge information today minus one day, select Loading plant, ItemType, Status.
    Return output as excel file export from Das System.

    """
    yesterday = datetime.today() - timedelta(days=1)

    yesterday = yesterday.strftime("%d/%m/%Y")

    LoadingPlant = "โรงงาน 2,โรงงาน 3"
    ItemType = "Bigbag,BAG,BULK"
    Status = "เสร็จสิ้น(Gate Outแล้ว)"

    ### Extract Data from outbound Gateout page ####
    driver.implicitly_wait(3)
    driver.get("http://10.224.29.107/cement/report/cement_weightbridge/rpt_weightbridge_cement")
    # Click to select dropdown
    driver.find_element_by_xpath("//*[@id='Export']/div[1]/span/span").click()
    #Click to select Gateout
    driver.find_element_by_xpath("//*[@id='_easyui_combobox_i5_3']").click()

    # Extract today data time (from - to) / date is the open file date

    dateFromTo = ["date_from","date_to"]

    for date in dateFromTo:
        # remove all hanging around message
        driver.find_element_by_xpath("//*[@id='show-msg']").click()
        dateInput = driver.find_element_by_id(date)
        dateInput.click()
        dateInput.clear()
        dateInput.send_keys(yesterday)

    timeFromTo = ["time_from","time_to"]
    for t in timeFromTo:
        # remove all hanging around message
        driver.find_element_by_xpath("//*[@id='show-msg']").click()
        timeInput = driver.find_element_by_id(t)
        timeInput.click()
        timeInput.clear()
        if t == "time_from":
            timeInput.send_keys("00:00")
        else:
            timeInput.send_keys("23:59")

    # Select LoadingPlant ItemType and Status
    xPathInput = [(LoadingPlant,"//*[@id='Export']/div[11]/span/input[1]"),
                    (ItemType,"//*[@id='Export']/div[14]/span/input"),
                    (Status,"//*[@id='Export']/div[18]/span/input")]

    for path in xPathInput:
        time.sleep(2)
        # select path to extract
        driver.find_element_by_xpath(path[1]).send_keys(path[0])
        # remove all hanging around message
        driver.find_element_by_xpath("//*[@id='show-msg']").click()

    # Click export excel
    driver.find_element_by_xpath("//*[@id='Export']/div[20]/div/a[2]/span/span").click()

def table(request):
    preDO = request.GET['PreDO']
    #query="select top 10 * from shipmenttracking"
    query="select top 10 * from shipmenttracking where PreDONo ='"+preDO+"'"
    df=sql_execute_query('sqldb-datawarehouse',query,None,True)
    tables = df.to_html()
    return HttpResponse(tables)

def table1(request):
    #preDO = request.GET['PreDO']
    #query="select top 10 * from shipmenttracking"
    #query="select top 10 * from shipmenttracking where PreDONo ='"+preDO+"'"
    #df=sql_execute_query('sqldb-datawarehouse',query,None,True)
    #tables = df.to_html()
    DasWBInfoExtract(DasPassword("autobot","password1*"))
    return HttpResponse('Hello')
