print('starting..')
from pyobigram.utils import sizeof_fmt,get_file_size,createID,nice_time
from pyobigram.client import ObigramClient,inlineQueryResultArticle
from MoodleClient import MoodleClient

from JDatabase import JsonDatabase
import zipfile
import os
import infos
import mediafire
import datetime
import time
import youtube
import NexCloudClient

from pydownloader.downloader import Downloader
from ProxyCloud import ProxyCloud
import ProxyCloud
import socket
import tlmedia
import S5Crypto


def downloadFile(downloader,filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        thread = args[2]
        if thread.getStore('stop'):
            downloader.stop()
        downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time,tid=thread.id)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def uploadFile(filename,currentBits,totalBits,speed,time,args):
    try:
        bot = args[0]
        message = args[1]
        originalfile = args[2]
        thread = args[3]
        downloadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
        bot.editMessageText(message,downloadingInfo)
    except Exception as ex: print(str(ex))
    pass

def processUploadFiles(filename,filesize,files,update,bot,message,thread=None,jdb=None):
    try:
        bot.editMessageText(message,'🤜𝐏𝐫𝐞𝐩𝐚𝐫𝐚𝐧𝐝𝐨 𝐩𝐚𝐫𝐚 𝐬𝐮𝐛𝐢𝐫☁...')
        evidence = None
        fileid = None
        user_info = jdb.get_user(update.message.sender.username)
        cloudtype = user_info['cloudtype']
        proxy = ProxyCloud.parse(user_info['proxy'])
        if cloudtype == 'moodle':
            client = MoodleClient(user_info['moodle_user'],
                                  user_info['moodle_password'],
                                  user_info['moodle_host'],
                                  user_info['moodle_repo_id'],
                                  proxy=proxy)
            loged = client.login()
            itererr = 0
            if loged:
                if user_info['uploadtype'] == 'evidence':
                    evidences = client.getEvidences()
                    evidname = str(filename).split('.')[0]
                    for evid in evidences:
                        if evid['name'] == evidname:
                            evidence = evid
                            break
                    if evidence is None:
                        evidence = client.createEvidence(evidname)

                originalfile = ''
                if len(files)>1:
                    originalfile = filename
                draftlist = []
                for f in files:
                    f_size = get_file_size(f)
                    resp = None
                    iter = 0
                    token = False
                    if user_info['token']!=0:
                       token = True
                    xdlink = False
                    if user_info['xdmode']!=0:
                    	xdlink = True
                    while resp is None:
                          if user_info['uploadtype'] == 'evidence':
                             fileid,resp = client.upload_file(f,evidence,fileid,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'draft':
                             fileid,resp = client.upload_file_draft(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'perfil':
                             fileid,resp = client.upload_file_perfil(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'blog':
                             fileid,resp = client.upload_file_blog(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          if user_info['uploadtype'] == 'calendar':
                             fileid,resp = client.upload_file_calendar(f,progressfunc=uploadFile,args=(bot,message,originalfile,thread),token=token,xdlink=xdlink)
                             draftlist.append(resp)
                          iter += 1
                          if iter>=10:
                              break
                    os.unlink(f)
                if user_info['uploadtype'] == 'evidence':
                    try:
                        client.saveEvidence(evidence)
                    except:pass
                return client
            else:
                bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐥𝐚 𝐩𝐚𝐠𝐢𝐧𝐚❌')
        elif cloudtype == 'cloud':
            tokenize = False
            if user_info['tokenize']!=0:
               tokenize = True
            bot.editMessageText(message,'🤜𝐒𝐮𝐛𝐢𝐞𝐧𝐝𝐨 ☁ 𝐄𝐬𝐩𝐞𝐫𝐞 𝐦𝐢𝐞𝐧𝐭𝐫𝐚𝐬... 😄')
            host = user_info['moodle_host']
            user = user_info['moodle_user']
            passw = user_info['moodle_password']
            remotepath = user_info['dir']
            client = NexCloudClient.NexCloudClient(user,passw,host,proxy=proxy)
            loged = client.login()
            if loged:
               originalfile = ''
               if len(files)>1:
                    originalfile = filename
               filesdata = []
               for f in files:
                   data = client.upload_file(f,path=remotepath,progressfunc=uploadFile,args=(bot,message,originalfile,thread),tokenize=tokenize)
                   filesdata.append(data)
                   os.unlink(f)
               return filesdata
        return None
    except Exception as ex:
        bot.editMessageText(message,f'❌𝐄𝐫𝐫𝐨𝐫 {str(ex)}❌')


def processFile(update,bot,message,file,thread=None,jdb=None):
    file_size = get_file_size(file)
    getUser = jdb.get_user(update.message.sender.username)
    max_file_size = 1024 * 1024 * getUser['zips']
    file_upload_count = 0
    client = None
    findex = 0
    if file_size > max_file_size:
        compresingInfo = infos.createCompresing(file,file_size,max_file_size)
        bot.editMessageText(message,compresingInfo)
        zipname = str(file).split('.')[0] + createID()
        mult_file = zipfile.MultiFile(zipname,max_file_size)
        zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
        zip.write(file)
        zip.close()
        mult_file.close()
        client = processUploadFiles(file,file_size,mult_file.files,update,bot,message,jdb=jdb)
        try:
            os.unlink(file)
        except:pass
        file_upload_count = len(zipfile.files)
    else:
        client = processUploadFiles(file,file_size,[file],update,bot,message,jdb=jdb)
        file_upload_count = 1
    bot.editMessageText(message,'😌𝐏𝐫𝐞𝐩𝐚𝐫𝐚𝐧𝐝𝐨 𝐚𝐫𝐜𝐡𝐢𝐯𝐨📄...')
    evidname = ''
    files = []
    if client:
        if getUser['cloudtype'] == 'moodle':
            if getUser['uploadtype'] == 'evidence':
                try:
                    evidname = str(file).split('.')[0]
                    txtname = evidname + '.txt'
                    evidences = client.getEvidences()
                    for ev in evidences:
                        if ev['name'] == evidname:
                           files = ev['files']
                           break
                        if len(ev['files'])>0:
                           findex+=1
                    client.logout()
                except:pass
            if getUser['uploadtype'] == 'draft' or getUser['uploadtype'] == 'blog' or getUser['uploadtype'] == 'calendar':
               for draft in client:
                   files.append({'name':draft['file'],'directurl':draft['url']})
        else:
            for data in client:
                files.append({'name':data['name'],'directurl':data['url']})
        bot.deleteMessage(message.chat.id,message.message_id)
        finishInfo = infos.createFinishUploading(file,file_size,max_file_size,file_upload_count,file_upload_count,findex)
        filesInfo = infos.createFileMsg(file,files)
        bot.sendMessage(message.chat.id,finishInfo+'\n'+filesInfo,parse_mode='html')
        if len(files)>0:
            txtname = str(file).split('/')[-1].split('.')[0] + '.txt'
            sendTxt(txtname,files,update,bot)
    else:
        bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐥𝐚 𝐩𝐚𝐠𝐢𝐧𝐚❌')

def ddl(update,bot,message,url,file_name='',thread=None,jdb=None):
    downloader = Downloader()
    file = downloader.download_url(url,progressfunc=downloadFile,args=(bot,message,thread))
    if not downloader.stoping:
        if file:
            processFile(update,bot,message,file,jdb=jdb)
        else:
            bot.editMessageText(message,'❌𝐄𝐧𝐥𝐚𝐜𝐞 𝐧𝐨 𝐩𝐫𝐨𝐜𝐞𝐬𝐚𝐝𝐨❌')

# def megadl(update,bot,message,megaurl,file_name='',thread=None,jdb=None):
#     megadl = megacli.mega.Mega({'verbose': True})
#     megadl.login()
#     try:
#         info = megadl.get_public_url_info(megaurl)
#         file_name = info['name']
#         megadl.download_url(megaurl,dest_path=None,dest_filename=file_name,progressfunc=downloadFile,args=(bot,message,thread))
#         if not megadl.stoping:
#             processFile(update,bot,message,file_name,thread=thread)
#     except:
#         files = megaf.get_files_from_folder(megaurl)
#         for f in files:
#             file_name = f['name']
#             megadl._download_file(f['handle'],f['key'],dest_path=None,dest_filename=file_name,is_public=False,progressfunc=downloadFile,args=(bot,message,thread),f_data=f['data'])
#             if not megadl.stoping:
#                 processFile(update,bot,message,file_name,thread=thread)
#         pass
#     pass

def sendTxt(name,files,update,bot):
                txt = open(name,'w')
                fi = 0
                for f in files:
                    separator = ''
                    if fi < len(files)-1:
                        separator += '\n'
                    txt.write(f['directurl']+separator)
                    fi += 1
                txt.close()
                bot.sendFile(update.message.chat.id,name)
                os.unlink(name)

def onmessage(update,bot:ObigramClient):
    try:
        thread = bot.this_thread
        username = update.message.sender.username
        tl_admin_user = os.environ.get('administrador')
        
        #set
        tl_admin_user = 'Zeta30'

        jdb = JsonDatabase('database')
        jdb.check_create()
        jdb.load()

        user_info = jdb.get_user(username)

        if username == tl_admin_user or user_info :  # validate user
            if user_info is None:
                if username == tl_admin_user:
                    jdb.create_admin(username)
                else:
                    jdb.create_user(username)
                user_info = jdb.get_user(username)
                jdb.save()
        else:return


        msgText = ''
        try: msgText = update.message.text
        except:pass

        # comandos de admin
        if '/add' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    jdb.create_user(user)
                    jdb.save()
                    msg = '😉𝐖𝐨𝐨𝐨𝐰 @'+user+' 𝐚𝐡𝐨𝐫𝐚 𝐭𝐢𝐞𝐧𝐞𝐬 𝐚𝐜𝐜𝐞𝐬𝐨 𝐚𝐥 𝐛𝐨𝐭 𝐒𝐩𝐞𝐞𝐝𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐫 𝐒𝐞𝐫𝐯𝐢𝐜𝐞 𝐯7.3'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌𝐍𝐨 𝐭𝐢𝐞𝐧𝐞𝐬 𝐩𝐞𝐫𝐦𝐢𝐬𝐨 𝐩𝐚𝐫𝐚 𝐞𝐬𝐭𝐨❌')
            return
        if '/ban' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                try:
                    user = str(msgText).split(' ')[1]
                    if user == username:
                        bot.sendMessage(update.message.chat.id,'❌𝐍𝐨 𝐬𝐞 𝐩𝐮𝐞𝐝𝐞 𝐛𝐚𝐧𝐞𝐚𝐫 𝐚 𝐮𝐬𝐭𝐞𝐝 𝐦𝐢𝐬𝐦𝐨❌')
                        return
                    jdb.remove(user)
                    jdb.save()
                    msg = '🤬𝐄𝐥 𝐮𝐬𝐮𝐚𝐫𝐢𝐨 @'+user+' 𝐚 𝐬𝐢𝐝𝐨 𝐛𝐚𝐧𝐞𝐚𝐝𝐨❌'
                    bot.sendMessage(update.message.chat.id,msg)
                except:
                    bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            else:
                bot.sendMessage(update.message.chat.id,'❌𝐍𝐨 𝐭𝐢𝐞𝐧𝐞𝐬 𝐩𝐞𝐫𝐦𝐢𝐬𝐨 𝐩𝐚𝐫𝐚 𝐞𝐬𝐭𝐨❌')
            return
        if '/db' in msgText:
            isadmin = jdb.is_admin(username)
            if isadmin:
                bot.sendMessage(update.message.chat.id,'🗂️𝐁𝐚𝐬𝐞 𝐝𝐞 𝐝𝐚𝐭𝐨𝐬👇')
                bot.sendFile(update.message.chat.id,'database.jdb')
            else:
                bot.sendMessage(update.message.chat.id,'❌𝐍𝐨 𝐭𝐢𝐞𝐧𝐞𝐬 𝐩𝐞𝐫𝐦𝐢𝐬𝐨 𝐩𝐚𝐫𝐚 𝐞𝐬𝐭𝐨❌')
            return

        if '/tuto' in msgText:
            tuto = open('tuto.txt','r')
            bot.sendMessage(update.message.chat.id,tuto.read())
            tuto.close()
            return

        if '/crypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy = S5Crypto.encrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'👤𝐄𝐧𝐜𝐫𝐲𝐩𝐭𝐚𝐝𝐨:\n{proxy}')
            return

        if '/decrypt' in msgText:
            proxy_sms = str(msgText).split(' ')[1]
            proxy_de = S5Crypto.decrypt(f'{proxy_sms}')
            bot.sendMessage(update.message.chat.id, f'🧑‍💼𝐃𝐞𝐬𝐞𝐧𝐜𝐫𝐲𝐩𝐭𝐚𝐝𝐨:\n{proxy_de}')
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'💔𝐏𝐫𝐨𝐱𝐲 𝐝𝐞𝐬𝐚𝐜𝐭𝐢𝐯𝐚𝐝𝐨 𝐜𝐨𝐧 𝐞𝐱𝐢𝐭𝐨')
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,'💔𝐏𝐫𝐨𝐱𝐲 𝐝𝐞𝐬𝐚𝐜𝐭𝐢𝐯𝐚𝐝𝐨 𝐜𝐨𝐧 𝐞𝐱𝐢𝐭𝐨')
            return
        if '/view_proxy' in msgText:
            try:


                getUser = user_info

                if getUser:
                    proxy = getUser['proxy']
                    bot.sendMessage(update.message.chat.id,proxy)
            except:
                if user_info:
                    proxy = user_info['proxy']
                    bot.sendMessage(update.message.chat.id,proxy)
            return
        if '/my' in msgText:
            getUser = user_info
            if getUser:
                statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                bot.sendMessage(update.message.chat.id,statInfo)
                return
        if '/zips' in msgText:
            getUser = user_info
            if getUser:
                try:
                   size = int(str(msgText).split(' ')[1])
                   getUser['zips'] = size
                   jdb.save_data_user(username,getUser)
                   jdb.save()
                   msg = '📚𝐋𝐨𝐬 𝐳𝐢𝐩𝐬 𝐬𝐞𝐫𝐚𝐧 𝐝𝐞 '+ sizeof_fmt(size*1024*1024)+' 𝐥𝐚𝐬 𝐩𝐚𝐫𝐭𝐞𝐬'
                   bot.sendMessage(update.message.chat.id,msg)
                except:
                   bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')    
                return
        if '/acc' in msgText:
            try:
                account = str(msgText).split(' ',2)[1].split(',')
                user = account[0]
                passw = account[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_user'] = user
                    getUser['moodle_password'] = passw
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/host' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                host = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['moodle_host'] = host
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/repo' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                repoid = int(cmd[1])
                getUser = user_info
                if getUser:
                    getUser['moodle_repo_id'] = repoid
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/xdlink_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/xdlink_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['xdmode'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/token_on' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['token'] = 1
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/token_off' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['token'] = 0
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/cloud' in msgText:
            try:
                cmd = str(msgText).split(' ')[0]
                getUser = user_info
                if getUser:
                    getUser['cloudtype'] = cmd
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/up' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                type = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['uploadtype'] = type
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                bot.sendMessage(update.message.chat.id,'❌𝐄𝐫𝐫𝐨𝐫 𝐞𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨❌')
            return
        if '/proxy' in msgText:
            try:
                cmd = str(msgText).split(' ',2)
                proxy = cmd[1]
                getUser = user_info
                if getUser:
                    getUser['proxy'] = proxy
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            return
        if '/off_proxy' in msgText:
            try:
                getUser = user_info
                if getUser:
                    getUser['proxy'] = ''
                    jdb.save_data_user(username,getUser)
                    jdb.save()
                    statInfo = infos.createStat(username,getUser,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            except:
                if user_info:
                    user_info['proxy'] = ''
                    statInfo = infos.createStat(username,user_info,jdb.is_admin(username))
                    bot.sendMessage(update.message.chat.id,statInfo)
            return
            
        if '/cancel_' in msgText:
            try:
                cmd = str(msgText).split('_',2)
                tid = cmd[1]
                tcancel = bot.threads[tid]
                msg = tcancel.getStore('msg')
                tcancel.store('stop',True)
                time.sleep(3)
                bot.editMessageText(msg,'❌𝐃𝐞𝐬𝐜𝐚𝐫𝐠𝐚 𝐜𝐚𝐧𝐬𝐞𝐥𝐚𝐝𝐚❌')
            except Exception as ex:
                print(str(ex))
            return
 
        message = bot.sendMessage(update.message.chat.id,'✌😜𝐀𝐧𝐚𝐥𝐢𝐳𝐚𝐧𝐝𝐨...')

        thread.store('msg',message)
        if '/start' in msgText:
            start_msg= '🤖𝐁𝐨𝐭: 𝐒𝐩𝐞𝐞𝐝𝐔𝐩𝐥𝐨𝐚𝐝𝐞𝐫 𝐒𝐞𝐫𝐯𝐢𝐜𝐞 𝐯7.3\n🎩𝐃𝐞𝐬𝐚𝐫𝐫𝐨𝐥𝐥𝐚𝐝𝐨𝐫: @xXxWTF_Dev\n🖋𝐃𝐢𝐬𝐞𝐧̃𝐚𝐝𝐨𝐫: @Jose_752\n🔥𝐓𝐨𝐝𝐨𝐬 𝐥𝐨𝐬 𝐜𝐨𝐦𝐚𝐧𝐝𝐨𝐬 𝐝𝐞𝐥 𝐛𝐨𝐭 𝐬𝐨𝐧 𝐜𝐨𝐦𝐩𝐥𝐞𝐭𝐚𝐦𝐞𝐧𝐭𝐞 𝐟𝐮𝐧𝐜𝐢𝐨𝐧𝐚𝐥𝐞𝐬 𝐚𝐬𝐢 𝐪𝐮𝐞 𝐭𝐞 𝐫𝐞𝐜𝐨𝐦𝐞𝐧𝐝𝐚𝐦𝐨𝐬 𝐪𝐮𝐞 𝐮𝐬𝐞𝐬 𝐞𝐥 /tuto'
            bot.editMessageText(message,start_msg)
        elif '/files' == msgText and user_info['cloudtype']=='moodle':
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 files = client.getEvidences()
                 filesInfo = infos.createFilesMsg(files)
                 bot.editMessageText(message,filesInfo)
                 client.logout()
             else:
                bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐲 𝐂𝐚𝐮𝐬𝐚𝐬😤\n1-𝐑𝐞𝐯𝐢𝐬𝐞 𝐬𝐮 𝐂𝐮𝐞𝐧𝐭𝐚\n2-𝐒𝐞𝐫𝐯𝐢𝐝𝐨𝐫 𝐃𝐞𝐬𝐚𝐛𝐢𝐥𝐢𝐭𝐚𝐝𝐨: '+client.path)
        elif '/txt_' in msgText and user_info['cloudtype']=='moodle':
             findex = str(msgText).split('_')[1]
             findex = int(findex)
             proxy = ProxyCloud.parse(user_info['proxy'])
             client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],proxy=proxy)
             loged = client.login()
             if loged:
                 evidences = client.getEvidences()
                 evindex = evidences[findex]
                 txtname = evindex['name']+'.txt'
                 sendTxt(txtname,evindex['files'],update,bot)
                 client.logout()
                 bot.editMessageText(message,'📄𝐓𝐱𝐓 𝐀𝐪𝐮𝐢👇')
             else:
                bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐲 𝐂𝐚𝐮𝐬𝐚𝐬😤\n1-𝐑𝐞𝐯𝐢𝐬𝐞 𝐬𝐮 𝐂𝐮𝐞𝐧𝐭𝐚\n2-𝐒𝐞𝐫𝐯𝐢𝐝𝐨𝐫 𝐃𝐞𝐬𝐚𝐛𝐢𝐥𝐢𝐭𝐚𝐝𝐨: '+client.path)
             pass
        elif '/del_' in msgText and user_info['cloudtype']=='moodle':
            findex = int(str(msgText).split('_')[1])
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfile = client.getEvidences()[findex]
                client.deleteEvidence(evfile)
                client.logout()
                bot.editMessageText(message,'🗑𝐀𝐫𝐜𝐡𝐢𝐯𝐨 𝐛𝐨𝐫𝐫𝐚𝐝𝐨🗑')
            else:
                bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐲 𝐂𝐚𝐮𝐬𝐚𝐬😤\n1-𝐑𝐞𝐯𝐢𝐬𝐞 𝐬𝐮 𝐂𝐮𝐞𝐧𝐭𝐚\n2-𝐒𝐞𝐫𝐯𝐢𝐝𝐨𝐫 𝐃𝐞𝐬𝐚𝐛𝐢𝐥𝐢𝐭𝐚𝐝𝐨: '+client.path)
        elif '/delall' in msgText and user_info['cloudtype']=='moodle':
            proxy = ProxyCloud.parse(user_info['proxy'])
            client = MoodleClient(user_info['moodle_user'],
                                   user_info['moodle_password'],
                                   user_info['moodle_host'],
                                   user_info['moodle_repo_id'],
                                   proxy=proxy)
            loged = client.login()
            if loged:
                evfiles = client.getEvidences()
                for item in evfiles:
                	client.deleteEvidence(item)
                client.logout()
                bot.editMessageText(message,'🗑𝐀𝐫𝐜𝐡𝐢𝐯𝐨𝐬 𝐝𝐞 𝐥𝐚 𝐧𝐮𝐛𝐞 𝐛𝐨𝐫𝐫𝐚𝐝𝐨𝐬🗑')
            else:
                bot.editMessageText(message,'❌𝐄𝐫𝐫𝐨𝐫 𝐲 𝐂𝐚𝐮𝐬𝐚𝐬😤\n1-𝐑𝐞𝐯𝐢𝐬𝐞 𝐬𝐮 𝐂𝐮𝐞𝐧𝐭𝐚\n2-𝐒𝐞𝐫𝐯𝐢𝐝𝐨𝐫 𝐃𝐞𝐬𝐚𝐛𝐢𝐥𝐢𝐭𝐚𝐝𝐨: '+client.path)       
        elif 'http' in msgText:
            url = msgText
            ddl(update,bot,message,url,file_name='',thread=thread,jdb=jdb)
        else:
            #if update:
            #    api_id = os.environ.get('api_id')
            #    api_hash = os.environ.get('api_hash')
            #    bot_token = os.environ.get('bot_token')
            #    
                # set in debug
            #    api_id = 18403498
            #    api_hash = '2c0b01283b1b67f7087a92cc81cd91f8'
            #    bot_token = '5458733719:AAE9KqQTcxF5sGY1nhv289tr-L2g7XezGeg'

            #    chat_id = int(update.message.chat.id)
            #    message_id = int(update.message.message_id)
            #    import asyncio
            #    asyncio.run(tlmedia.download_media(api_id,api_hash,bot_token,chat_id,message_id))
            #    return
            bot.editMessageText(message,'😤𝐍𝐨 𝐬𝐞 𝐩𝐮𝐝𝐨 𝐩𝐫𝐨𝐜𝐞𝐬𝐚𝐫😤')
    except Exception as ex:
           print(str(ex))
print('Ready')
def main():
    bot_token = os.environ.get('bot_token')
    
    #set
    bot_token = '5458733719:AAE9KqQTcxF5sGY1nhv289tr-L2g7XezGeg'

    bot = ObigramClient(bot_token)
    bot.onMessage(onmessage)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except:
        main()

