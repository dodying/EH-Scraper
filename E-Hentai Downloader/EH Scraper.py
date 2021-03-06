# -*- coding: UTF-8 -*-
# ==Headers==
# @Name:               EH Scraper
# @Description:        EH Scraper
# @Version:            1.0.0
# @Author:             dodying
# @Date:               2018-02-14 10:10:01
# @Last Modified by:   dodying
# @Last Modified time: 2018-06-02 13:54:26
# @Namespace:          https://github.com/dodying/EH-Scraper
# @SupportURL:         https://github.com/dodying/EH-Scraper/issues
# @Import:
# ==/Headers==

#@Name  EH Scraper
#@Key   EH_Scraper
#@Image EH.png
#@Hook  Books

import clr
import re

clr.AddReference("System")
from System.IO import StreamReader, Directory
from System.Text import UTF8Encoding
# from System.Net import WebRequest
# from System.Text import Encoding

clr.AddReference("Ionic.Zip.dll")
from Ionic.Zip import ZipFile

clr.AddReference('System.Web.Extensions')
from System.Web.Script.Serialization import JavaScriptSerializer

_dir = Directory.GetParent(__file__).FullName
EHT_File = open(_dir + '\\EHT.json', 'r')
EHT = EHT_File.read()
EHT_File.close()
EHT = dict(JavaScriptSerializer().DeserializeObject(EHT))['dataset']

def EH_Scraper(books):
  for book in books:
    # ((cYo.Projects.ComicRack.Engine.ComicBook)book).FileLocation
    with ZipFile.Read(book.FileLocation) as zipfile:
      for i in zipfile.Entries:
        if re.search('info.txt', i.FileName):
          infoFile = i.FileName
          with StreamReader(zipfile[infoFile].OpenReader(), UTF8Encoding) as stream:
            contents = stream.ReadToEnd()
            info = parseInfoContent(contents)
            try:
              info = parseInfoContent(contents)
            except:
              print
            else:
              for i in info:
                setattr(book, i, info[i])
            # result = re.search('g/(\d+)/(\w+)/', contents)
            # gid = result.group(1)
            # token = result.group(2)

def parseInfoContent(text):
  info = {}
  text = re.sub('(Page|Image) \\d+: .*','', text)
  text = re.sub('(Downloaded at|Generated by).*', '', text)
  text = re.sub('([\r\n]){2,}', '\n', text)
  text = re.sub('[\r\n]+$', '', text)
  text = re.sub('[\r\n]+> ', '\n', text)
  a = re.compile('[\r\n]+').split(text)
  b = {}

  for i in a:
    t = i.split(': ')
    if len(t) > 1:
      b[t[0]] = t[1]

  a[0] = a[0].strip()
  info['Title'] = a[0]
  t = re.sub('\\[.*?\\]|\\(.*?\\)|\\{.*?\\}|【.*?】', '', a[0]).strip()
  if re.search('(\d+\.|)[0-9]+$', t) and float(re.search('(\d+\.|)[0-9]+$', t).group()) <= 1000:
    if re.search('\d+\.[0-9]+$', t) and re.search('\d+\.[1-9]+$', t):
      info['Number'] = str(float(re.search('\d+\.[1-9]+$', t).group()))
    elif re.search('\d+\.[0-9]+$', t) and re.search('\d+\.0+$', t):
      info['Number'] = str(int(re.search('\d+', re.search('\d+\.0+$', t).group()).group()))
    else:
      info['Number'] = str(int(re.search('\d+$', t).group()))
    info['Series'] = re.sub('%s$' % info['Number'], '' , t).strip()
  else:
    info['Number'] = '1'
    info['Series'] = t or a[0]

  for i in a:
    if re.search('^http', i):
      if re.search('/g/\d+/.*?/', i):
        # info['Series'] = re.search("\d+", i).group()
        # info['Number'] = '1'
        info['Web'] = 'https://exhentai.org' + re.search("/g/\d+/.*?/", i).group()
      else:
        info['Web'] = i
      break

  # if 'parody' in b:
  #   info['Series'] = findData('parody', b['parody']) or b['parody']

  if 'Uploader Comment:' in a:
    if a.index('Tags:') >= 0 and a.index('Uploader Comment:') < a.index('Tags:'):
      info['Summary'] = '\n'.join(a[a.index('Uploader Comment:') : a.index('Tags:')])
    else:
      info['Summary'] = '\n'.join(a[a.index('Uploader Comment:') :])

  if 'character' in b:
    info['Characters'] = findData('character', b['character']) or b['character']

  if 'artist' in b:
    info['Writer'] = findData('artist', b['artist']) or b['artist']
  elif 'group' in b:
    info['Writer'] = findData('group', b['group']) or b['group']

  if re.search('FREE HENTAI', b['Category']):
    info['Genre'] = re.search('FREE HENTAI (.*?) GALLERY', b['Category']).group(1)
  else:
    info['Genre'] = b['Category']

  if re.search('Chinese', b['Language']):
    info['LanguageISO'] = 'zh'
  elif re.search('English', b['Language']):
    info['LanguageISO'] = 'en'
  else:
    info['LanguageISO'] = 'jp'

  if 'Rating' in b and re.search('[\\d\\.]+', b['Rating']):
    info['CommunityRating'] = float(b['Rating'])

  info['Tags'] = []
  for i in ['language', 'parody', 'character', 'group', 'artist', 'male', 'female', 'misc']:
    if i in b:
      t = re.compile(',(\\s+|)').split(b[i])
      t = filter(lambda j: not(re.search('^\\s+$', j)), t)
      t = map(lambda j: (findData(i) or i) + ': ' + (findData(i, j) or j), t)
      info['Tags'] = info['Tags'] + t
  if len(info['Tags']) > 0:
    info['Tags'] = ','.join(info['Tags'])
  else:
    del info['Tags']

  if 'Posted' in b:
    date = re.search('(\\d{4})-(\\d{1,2})-(\\d{1,2})', b['Posted'])
    info['Year'] = int(date.group(1))
    info['Month'] = int(date.group(2))
    info['Day'] = int(date.group(3))
    #info['Published'] = b['Posted']

  if 'Uploader' in b:
    info['Publisher'] = b['Uploader']


  return info

def scrapeFromEH(gid, token):
  parm = '{"method":"gdata","gidlist":[[' + gid + ',"' + token + '"]],"namespace":1}'

  req = WebRequest.Create("https://e-hentai.org/api.php")
  req.Method = "POST"
  req.ContentType = "application/x-www-form-urlencoded"
  req.UserAgent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Mobile Safari/537.36"

  parmBytes = Encoding.ASCII.GetBytes(parm)
  req.ContentLength = parmBytes.Length
  reqStream = req.GetRequestStream()
  reqStream.Write(parmBytes, 0, parmBytes.Length)
  reqStream.Close()

  response = req.GetResponse()
  result = StreamReader(response.GetResponseStream()).ReadToEnd()
  data = dict(JavaScriptSerializer().DeserializeObject(result))
  data = dict(data['gmetadata'][0])
  return data

def combineText(arr):
  try:
    arr = list(arr)
  except:
    return ''
  else:
    arr = filter(lambda i: i['type'] == 0, arr)
    arr = map(lambda i: i['text'], arr)
    return '\\A'.join(arr)

def findData(main, sub = False):
  data = filter(lambda i: i['name'] == main, EHT)
  if len(data) == 0 or len(data[0]['tags']) == 0:
    return {}
  if sub == False:
    return combineText(data[0]['cname']).decode('utf-8')
  data = filter(lambda i: i['name'] == sub.replace('_', ' '), data[0]['tags'])
  if len(data) == 0:
    return {}
  return combineText(data[0]['cname']).decode('utf-8')
