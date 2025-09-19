# -*- coding:utf-8 -*-
#!/usr/bin/python3

import warnings 
warnings.filterwarnings("ignore", category=UserWarning, module="cryptography")


import paramiko, telnetlib, threading, xlrd, time, os,shutil, pystray, pyautogui,io
from apscheduler.schedulers.background import BackgroundScheduler
from tkinter import Tk, ttk, StringVar, filedialog, Toplevel, Label, Button
from PIL import ImageTk, Image
from pystray import MenuItem, Menu
from pathlib import Path
from datetime import datetime, timedelta

socket_count = 1

def get_hostfile_path():
    hostfile_path = filedialog.askopenfilename()
    if hostfile_path:
        var_hostpath.set(hostfile_path)


def set_result_path():
    result_path = filedialog.askdirectory()
    if result_path:
        var_resultpath.set(result_path)


def set_cmd_path():
    cmd_path = filedialog.askdirectory()
    if cmd_path:
        var_cmdpath.set(cmd_path)

def switchBt():
    global dayscom
    global daystime

    dayscom = int(var_dayscom.get())
    daystime = str(var_daystime.get())

    if not B3["state"] == "normal":    
        B0["state"] = "disabled"
        B1["state"] = "disabled"
        B2["state"] = "disabled"            
        B3["state"] = "disabled"
        E0["state"] = "disabled"
        E1["state"] = "disabled"
        E2["state"] = "disabled"
        E3["state"] = "disabled"
        E4["state"] = "disabled"
        E5["state"] = "disabled"
        E6["state"] = "disabled"
        E7["state"] = "disabled"
        scheduler = BackgroundScheduler()
        scheduler.add_job(thread_start, 'interval', days=dayscom, start_date=daystime)
        scheduler.start()

def delete_old_files(dst_dir,daysget):
    now = datetime.now()
    cutoff = now - timedelta(days=daysget)
    sub_dir = Path(dst_dir)
    for dirname in sub_dir.iterdir():
        if "Report" in dirname.name and sub_dir.joinpath(dst_dir, dirname).is_dir():  # dirname.name === str(dirname) 等价
            dir_time = datetime.fromtimestamp(dirname.stat().st_mtime)
            if dir_time < cutoff:
                shutil.rmtree(dirname)


def status_update(itemid, deviceID, hostname, hostip, status_str):
    tree.delete(itemid)
    tree.insert('', deviceID, iid=itemid, values=(deviceID, hostname, hostip, status_str))
    tree.update()

def status_sort(col_id):
    item_list = []
    for iid in tree.get_children():
        item_list.append((iid, tree.set(iid, column=col_id)))
#    item_list.sort(key=lambda x: x[1])    # 需要01，02..20
    item_list.sort()                       # 1，2，3，..20
    for index, (iid, _) in enumerate(item_list):
        tree.move(iid, '', index)
#    return item_list

def thread_start():
    global en_device
    global rootpath
    global socket_count
    global su_device
    global wait_time
    global daysget

    if tree.get_children():
        for pre_item in tree.get_children():
            tree.delete(pre_item)

    src_excel = var_hostpath.get()
    dst_dir = var_resultpath.get()
    cmd_dir = var_cmdpath.get()
    wait_time = float(var_time.get())
    socket_max = int(var_socket_max.get())
    daysget = int(var_daysget.get())

    hostfile = xlrd.open_workbook(src_excel)
    table_list = hostfile.sheet_by_name('Sheet1')
    rows = table_list.nrows
 #   cols = table_list.ncols
    en_device = ['Cisco','CISCO','cisco','思科','maipu', '迈普','DPtech','迪普','ruijie','RuiJie','锐捷','ZX','中兴']
    su_device = ['H3C','h3c','H3c','huawei','HUAWEI','Huawei','华三','华为']
    rootpath = dst_dir + '//Report_' + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    dir_path = Path(rootpath)
    if dir_path.exists():
        shutil.rmtree(rootpath)
    else:
        os.makedirs(rootpath)

    delete_old_files(dst_dir,daysget)
    
    for j in range(1, rows):
        while 1:
            if socket_count <= socket_max:
                socket_count += 1
                break
            if socket_count > socket_max:
                tree.update()


        deviceID = str(j)
        hostname = table_list.cell(j, 0).value
        hostip_tmp = str(table_list.cell(j, 1).value)
        hostip = hostip_tmp.strip()
        username_tmp = str(table_list.cell(j, 2).value)
        username = username_tmp.strip()
        password = str(table_list.cell(j, 3).value)
        superpass = str(table_list.cell(j, 4).value)
        devicetype = table_list.cell(j, 5).value
        cmdfile = table_list.cell(j, 6).value
        loginmode = table_list.cell(j, 7).value
        port_map = table_list.cell(j, 8).value
        itemid = tree.insert('', deviceID, values=(deviceID, hostname, hostip, 'stanby'))
        tree.update()


        try:
            cmdfile_path = '%s\\%s' % (cmd_dir, cmdfile)
            cmdfile_str = open(cmdfile_path)
            cmdlist = cmdfile_str.readlines()
            if not cmdlist[-1].endswith('\n'):
                cmdlist[-1] += '\n'
            cmdfile_str.close()
        except:
            socket_count -= 1
            status_update(itemid, deviceID, hostname, hostip, 'no cmd files')
            continue

        if 'ssh' in loginmode:
            threading.Thread(target=ssh_main, args=(itemid, deviceID, hostname, hostip, cmdlist, username, password, superpass, devicetype, port_map)).start()

        elif 'telnet' in loginmode:
            threading.Thread(target=telnet_main, args=(itemid, deviceID, hostname, hostip, cmdlist, username, password, superpass, devicetype, port_map)).start()

        else:
            status_update(itemid, deviceID, hostname, hostip, 'unkown login method')
#        tree.see(itemid)   #用于滚动treeview控件，以便使指定的项可见。如果指定的项已经可见，则不会发生任何事情。这个方法接受一个参数：itemid，表示要滚动到的项的ID


    while True:
        if socket_count == 1:
            status_sort(0)
            time.sleep(1)
            with open(rootpath + '\\logging.log', 'w') as logging_file:
                for iid in tree.get_children():
                    logging = tree.set(iid)
                    for k, v in logging.items():
                        logging_file.write(v + '    ')
                    logging_file.write('\n')
                    logging_file.flush()
                break
        else:
            tree.update()


def ssh_main(itemid, deviceID, hostname, hostip, cmdlist, username, password, superpass, devicetype, port_map):
#    import pdb;pdb.set_trace()
    global socket_count
    if not port_map:
        port_map = 22
    else:
        port_map = int(port_map)
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        status_update(itemid, deviceID, hostname, hostip, 'ssh connect...')
        ssh.connect(hostip, port_map, username, password, timeout=20)
    except:
        socket_count -= 1
        status_update(itemid, deviceID, hostname, hostip, 'ssh failed')
        ssh.close()
    else:
        sshell = ssh.invoke_shell()
        time.sleep(2)
        if superpass !='' :
            if devicetype in en_device:
                sshell.send('enable\n')
                time.sleep(2)
                sshell.send(superpass + '\n')
                sshell.send('\n')
            if devicetype in su_device:
                sshell.send('super\n')
                time.sleep(2)
                sshell.send(superpass + '\n')
                sshell.send('\n')
        time.sleep(2)
        time.sleep(wait_time)
        status_update(itemid, deviceID, hostname, hostip, 'running')
#        status_sort(0)
        time.sleep(1)
        result_file = open(rootpath + '\\' + hostip + '_' + hostname.rstrip('\n') + '.log', 'ab')
        login_str = sshell.recv(1024)
        result_file.write(login_str)
        result_file.flush()
        if b'expired' in login_str:
            ssh.close()
            socket_count -= 1
            status_update(itemid, deviceID, hostname, hostip, 'password expired')
        if b'aged out' in login_str:
            ssh.close()
            socket_count -= 1
            status_update(itemid, deviceID, hostname, hostip, 'password ageout')
        else:
            for cmdstring in cmdlist:
                sshell.send(cmdstring)
                while True:
                    time.sleep(wait_time)
                    time.sleep(1)
                    if sshell.recv_ready():
                        result_z = sshell.recv(102400)
                        result_file.write(result_z)
                        result_file.flush()
                    else:
                        break

            result_file.close()
            ssh.close()
            status_update(itemid, deviceID, hostname, hostip, 'done')
            socket_count -= 1
            


def telnet_main(itemid, deviceID, hostname, hostip, cmdlist, username, password, superpass, devicetype, port_map):
#   import pdb;pdb.set_trace()
    global socket_count
    if not port_map:
        port_map = 23
    else:
        port_map = int(port_map)
    try:
        status_update(itemid, deviceID, hostname, hostip, 'telnet connect...')
        tn = telnetlib.Telnet(hostip, port_map)
    except:
        socket_count -= 1
        status_update(itemid, deviceID, hostname, hostip, 'telnet failed')
    else:
        time.sleep(2)
        time.sleep(wait_time)
        login_temp1 = tn.read_very_eager()
        if b'assword:' in login_temp1:
            tn.write(password.encode('ascii') + b'\n')
        else:
            tn.write(username.encode('ascii') + b'\n')
            time.sleep(2)
            time.sleep(wait_time)
            tn.read_until(b'assword:')
            tn.write(password.encode('ascii') + b'\n')
        time.sleep(2)
        if superpass !='':
            if devicetype in en_device:
                tn.write(b'enable\n')
                time.sleep(2)
                tn.write(superpass.encode('ascii') + b'\n')
            if devicetype in su_device:
                tn.write(b'super\n')
                time.sleep(2)
                tn.write(superpass.encode('ascii') + b'\n')
        time.sleep(2)
        time.sleep(wait_time)
        login_temp2 = tn.read_very_eager()
        logstr = login_temp1 + login_temp2
        with open(rootpath + '\\' + hostip + '_' + hostname.rstrip('\n') + '.log', 'ab') as result_file:
            result_file.write(logstr)
            result_file.flush()
        status_update(itemid, deviceID, hostname, hostip, 'running')
#        status_sort(0)
        time.sleep(1)
        for cmdstring in cmdlist:
            tn.write(cmdstring.encode('ascii'))
            while True:
                time.sleep(wait_time)
                time.sleep(1)
                res_str = tn.read_very_eager()
                if str(res_str) == str(b''):
                    break
                else:
                    with open(rootpath + '\\' + hostip + '_' + hostname.rstrip('\n') + '.log', 'ab') as result_file:
                        result_file.write(res_str)
                        result_file.flush()
        result_file.close()
        tn.close()
        status_update(itemid, deviceID, hostname, hostip, 'done')
        socket_count -= 1

def quit_window(icon: pystray.Icon):
    icon.stop()
    root.destroy()

def show_window():
    root.deiconify()
    # 获取当前窗口的句柄
    window = pyautogui.getWindowsWithTitle(root.title())[0]
    # 恢复窗口
    window.restore()

def hide_window():
    notify(icon)
    # 获取当前窗口的句柄
    window = pyautogui.getWindowsWithTitle(root.title())[0]
    # 最小化窗口
    window.minimize()
    root.withdraw()

def notify(icon: pystray.Icon):
    icon.notify("程序将后台继续运行", "SshTelnet批量工具 v1.6 GUI后台版")


if __name__ == '__main__':
    __version__ = "1.6.0.0"
    root = Tk()
    root.resizable(0, 0)
#    screenWidth = root.winfo_screenwidth() # 获取显示区域的宽度
#    screenHeight = root.winfo_screenheight() # 获取显示区域的高度
#    left = (screenWidth - root.winfo_reqwidth()) / 2 # 宽度x高度+偏移量
#    top = (screenHeight - root.winfo_reqheight()) / 2
#    root.geometry('+%d+%d' % (left, top))
    root.update()
#pyinstall编译时窗口图标可用    
    import base64
    from icon import img
    tmp = open("tmp.ico","wb+")
    tmp.write(base64.b64decode(img))
    tmp.close()
    root.iconbitmap("tmp.ico")
    os.remove("tmp.ico")
#pyinstall编译时窗口图标可用  
    root.title('SshTelnet批量工具 v1.6 GUI后台版')    
    L0 = ttk.Label(root, text='设备清单表格：').grid(row=0, sticky='E')
    L1 = ttk.Label(root, text='结果保存目录：').grid(row=1, sticky='E')
    L2 = ttk.Label(root, text='CMD目录路径：').grid(row=2, sticky='E')
    L3 = ttk.Label(root, text='缓冲延迟时间：').grid(row=3, sticky='E')
    L4 = ttk.Label(root, text='同时执行条数：').grid(row=4, sticky='E')
 
    L5 = ttk.Label(root, text='删除：').place(x=230,y=81)
    L6 = ttk.Label(root, text='天前日志目录').place(x=305,y=81)

    L7 = ttk.Label(root, text='每隔：').place(x=230,y=101)
    L8 = ttk.Label(root, text='天重复执行').place(x=305,y=101)

    L9 = ttk.Label(root, text='开始执行时间：')
    L9.grid(row=5, sticky='E')
 
    var_hostpath = StringVar()
    var_resultpath = StringVar()
    var_cmdpath = StringVar()
    var_time = StringVar()
    var_socket_max = StringVar()
    var_daysget = StringVar()
    var_dayscom = StringVar()
    var_daystime = StringVar()
    var_hostpath.set(os.getcwd() + '\\host.xlsx')
    var_resultpath.set(os.getcwd())
    var_cmdpath.set(os.getcwd() + '\\cmd')
    var_time.set(float('0.0'))
    var_socket_max.set(int(20))
    var_daysget.set(int(14))
    var_dayscom.set(int(7))
#    var_daystime.set('2023-01-01 00:00:00')
    later = datetime.fromtimestamp(time.time()) + timedelta(minutes=1) #当前时间增加1分钟
    var_daystime.set(later.strftime('%Y-%m-%d %H:%M:%S'))

    E0 = ttk.Entry(root, textvariable=var_hostpath, width=55)
    E0.grid(row=0, column=1, sticky='W')
    E1 = ttk.Entry(root, textvariable=var_resultpath, width=55)
    E1.grid(row=1, column=1, sticky='W')
    E2 = ttk.Entry(root, textvariable=var_cmdpath, width=55)
    E2.grid(row=2, column=1, sticky='W')
    E3 = ttk.Entry(root, textvariable=var_time, width=5)
    E3.grid(row=3, column=1, sticky='W')
    E4 = ttk.Entry(root, textvariable=var_socket_max, width=5)
    E4.grid(row=4, column=1, sticky='W')
    E5 = ttk.Entry(root, textvariable=var_daysget, width=5)
    E5.place(x=265,y=81)
    E6 = ttk.Entry(root, textvariable=var_dayscom, width=5)
    E6.place(x=265,y=101)
    E7 = ttk.Entry(root, textvariable=var_daystime, width=18)
    E7.grid(row=5, column=1, sticky='W')

    B0 = ttk.Button(root, text='选择文件', command=get_hostfile_path)
    B0.grid(row=0, column=2, sticky='W')
    B1 = ttk.Button(root, text='保存目录', command=set_result_path)
    B1.grid(row=1, column=2, sticky='W')
    B2 = ttk.Button(root, text='CMD路径', command=set_cmd_path)
    B2.grid(row=2, column=2, sticky='W')
    
    B3 = ttk.Button(root, text='开始运行', command=switchBt)
    B3.grid(row=3, column=2, rowspan=3, sticky='W')

    tree = ttk.Treeview(root)
    tree['columns'] = ('ID', 'hostname', 'hostip', 'status')
###################
    tree.column('ID')
    tree.column('hostname')
    tree.column('hostip')
    tree.column('status')
    tree.heading('ID',command=(lambda: status_sort(0)))
    tree.heading('hostname',command=(lambda: status_sort(1)))
    tree.heading('hostip',command=(lambda: status_sort(2)))
    tree.heading('status', command=(lambda: status_sort(3)))
    s1 = ttk.Scrollbar(root)
    s1.config(command=(tree.yview))
    tree.config(yscrollcommand=(s1.set))
##################    
    menu = (MenuItem('显示', show_window, default=True),Menu.SEPARATOR,MenuItem('退出', quit_window))
    image = Image.open(io.BytesIO(b'\x00\x00\x01\x00\x03\x00\x10\x10\x00\x00\x00\x00 \x00\xec\x02\x00\x006\x00\x00\x00\x18\x18\x00\x00\x00\x00 \x00P\x05\x00\x00"\x03\x00\x00  \x00\x00\x00\x00 \x00\x06\x07\x00\x00r\x08\x00\x00\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x02\xb3IDATx\x9cM\x92KHTQ\x1c\xc6\xff\xe7\x7f\xce}\xcc\xdcI\xc7l,\xeca\x05JZ\x14\x18\xb6p6\xbd\xa1\x82\xa0]\x9b(\x08\x02\xb3\x17FF\x0b\x89\x16\x85\x15\xb5(\x82^Pm\xa2$\nZ\xf4\xa0\xd0\xc8\x08\xa2B\x18\xb3\xc4\x92Hmf2_\xa33s\xef\xdc{\xce\xf9\xb7\x98\x88\xbe\xe5\xc7\xef\xb7\xf9\xf8\x00\x00\x10\x11\x11\x01\x00\x00Z[[\xc7F\x93\xa9\xb1\xecP*3\xf8\xb5\xaf\xb9y\x7f\xb1\xe7\x9c\xffe\x84\x10\xc5\xaa\xb11\xde\xfd\xea\x05\x11u\xf6dN\xdcL\xb5\xdd\xf8\xf5\xe6\xe3\x8cT\xfa\xe1\xa3\xfb\xf5\xf5\xab\xffi\x0c\x00\xe2\xf1\xf8\xf1cG7l\xdc84\xe5<\xe8L\x8f\xfc\xc60\xe3B\x92\xcc\x05\x8bc\xb0}\xcb\\#\x94\xea\xea\xea<\x7f\xf6b"\x91`MMM\xe7\xce\xb6{Xr\xfb\xc9\xe8\xfb/~\xd4\xb4\xca-`\x81\x12\x01\t\x052\xa7\xd1\x0fV\xae\x08o\xdaQ\x91\r\xd2\x87\x0e\x1ef\xbe\x97\x1dH\xc2\xe9\xbbc\xda\xb7l\t6Q\xd4f! \x1e\x10\x0f\xc8P\xc4%\x04\x99 ,\xf4\xd6\xe6\xb2\xc4P\x17\xbanv|\xb2\xc0\xf2f\x05g;7\x87\xaaJ\xc9M\x07\x98\xd5\xa6G\xa6G\xc2%\xc3\xd5Q\x93\xd9\x05\x9c\xf9\xed\xe5\xdd\x1c"\xa2\xc5\x98#\x15d$\xbaj\xdf\xde\xf2\x05Q*\xa4%\xcf+\xc3\xd3fA\xd9R\xdaJ\xceBe\x19\x0c\x10\x91\x18C\x05\x96K\x11\x82\xe7\x1d\xd3\x1f:\xa7\xf7\x1c\x88\xcd\x8f\x01MH;\x90\x0e(\x87i\x07t\x98\x14\'\r\x00\x02\x00\x98"\xcbS\xb6\xc9X^O\x0c\xcbH\x94Gm\x15\xe4\xa5A`\n\x1d\x12`\x19`\x01\x15\xe7\x17\x1a\x88\x13\x84}BW6\xc4\x9dM\xbb\xcb\x9e]\x1c\x99\x1e\x08\x96.\xb7L \x13\x89\xfb\x8a\xc6\x0b6\x00\x07\xd2\x04\x821F\x05%\xb2\xaa\xc4\xe1u\rV\xf7\x8d\x9f\xa3\xef\n\xf3\x97\x9akv\x95\x19!\xce\x05\x9b\xfa<\x9d\xbe\x97\x0b+\xe2J\x0bC\x08M\x10\xab\x08\x97\x9a\x93|F\xbd\xbd\xf2\xcb\x904\xaf\x1cq\xaa\xd0{a\xd8Dmq\xb2\xa4vr\xfe\xec9\x8eUf\x8e\r\x8e\xe3\xa1\xe6\x96\xc0N\xef>\xbfd\xd5\xba\xd2\x90/K@9\xa8"\xa8#\x92fI\x88d\xa4\xe3\xca\xaa\r\x95\xc6\xfe\xf2\x9eL_\xfb\xa93\x0c\x00\x16-\xaa:\xdcr`\xfd\xdau\x0b\xb1\xf6\xfb\x83\xb4\xd7\x9f\t[\xccB2}\x19\xad+\x8dl\x8b}\x82\xc1\xb6\x93m\xdd/_\xbb\x9e\x0b\x9c\xf3\xe2\xb1j\xaak\xee\xdc\xbd5\xfcc$\xf94\xf9\xedHb\xa4\xa57\xf3,5\xf0\xb9\xff\xd2\xb5\xcb\xb5\xcbj\xe1\xff0\xc6\x8a\x1a2^]S\xdd\xf1\xb8c\xf2\xfb\xf8h\x7f\xf2\xea\x9d\xeb\x95\x0b*\x11\xb0\xc8\x14\xe1?\x07iN\x98\xef\xab\xd6\xd5\x00\x00\x00\x00IEND\xaeB`\x82\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x18\x00\x00\x00\x18\x08\x02\x00\x00\x00o\x15\xaa\xaf\x00\x00\x05\x17IDATx\x9cmU[l]\xc5\x15]{\xcf\xcc9\xe7\xda\xb97\xb6\xe3b\xf2\xe0\xda@B%p[J#P\xc2C\x10\t\xab \x81\x08I\xa5\xb6HUx\xb4\xa8\xd4R\x82\xd2\x8fJ\x05E\x02B\xd2*\xe4\x8b\x1f\x84\x08\x08\x84D Q\x05\xc4\x18\x88\x91\x02\xc4\x14Q\x08B5\x85J\xa9S;ub\xfb\xfa\xda1\xf6}\x9d3\xb3w?n\x02A\xca\xfa\xda\x1f{\xad\xd9k\xb4g\r\xf0}Xk\x01\x18c\xfa\xfa\xfaFF\xbe\x9c)M\x86\x10|\xf0_\x7f5288\xb8a\xc3\x86\xf3\xdb.\x00f&\xa2f\xdd\xd3s\xe9\x81\x03\x07UU5\x8cOU\xf6\rN\xee\x1b,\x9d\x9c\xac\x894\xaa\xd5\xca3\xcf<\xbb|\xf9\n\x00Dt>\x8b\x9a\xe7\x87\x10\x008\x17\xfd\xf9\x91G~q\xf7\xc6+{{OM\x9f\xf9\xf4x8:R_\xa8X\xa3\xd4\x11\xfb\xf5\xbd\xb9\xde\xd5\xbaje\xc7\xc0\xc0\xa1\x0f?8\xba\xe7\xa9=MV\x93N\xd6Z\xef}wOO__\xdf\x83\xbf{\xf0\x87kzZ\xf2\x1dG\x8eM\x0f\x7f\xe5O\x959a\x1b\x01,*\r\x95\x86_\xb9\x0c\xd7^m\xaf\xbb\xee\xa2\xd3\x93c\x7f\xff\xe8\x93\x81C\x03\x87\x06\x0e\x95\xcbec\x0c\x01X\xbbv\xed\xc1\x83\x07\x8b\xc5" _\x8cV\xde\x18\x9e\x1f\x9d\xe4|\xec\x12"\nJ^X`\x02\x8ch\xa8\x0b\x87py7_\x7fs[\xf7jkM|\xe4\xfd#\x7f\xdc\xbe\xfd\xb3\xcf\x8e\xd1\x8e\x1d;\xfa\xfb\xfb;;;G\'\xce\xbcs\xac\xfe\xd1\xbf\xb2,\x8dZ-/1\x9a3\xa0\xa06(\x0b8(\x075\x01\x1c\xe0\xab!\xb1\xfe\xaa\xab\x93\xde\xeb\xe3\xe5\xddKfJs\xfd\xfd\x7f\xa0\x89\x89S\x9d\x1d\x85\xcfOd\xfb\xdeY\x98[\xb0-l\xac(\x07\xb5\x82V\x8b\x9c%\xf6\xdfJ\x08\x05XQ#@\xaa\xa1\x96\xe5\x0bz\xdb}+J~\xe4\x93\x8f?\xb5"\xc2\xa4\xa3\x13~n\xce\xb4\xc5\x86\xbc\xb6Z\r\x99\x84:\x84!\x0cg\x88\x834g1AM\x10\x0e\xc4As\xce\xa4S\xd9\x99\x93\xc1_\x94\x8a\xc2\x12\x01\x84\x98)\'\xca\r1A~\xb3\xa9\xcd\xd7\xfd+\xaf\xccQ\xcd(\x01\x0cw\xd6#8({5\xa2\xac\xeaH\x9d\x95\xc8\xa1\xceL\x0077\x80\x83\xbaT\xe3\x00n\xc8\xe8\xbf+?\xbb&\xff\xcb\xcdK\x13\xf5TST\x05Uu)L\xaa&U\xe7\xe1D\x12H\x02\x894X\xd5\xe6\x12Y\x00J0A]&\x8e\x84\x85\x8e\x0eU\xa8!\x1b\x7f\xd5e\x15\x03\xcf\xcf\xa2n@B\x0cG`\xa8\x83Z\x88U\x8d\x00U5\n\x05\x14\xb0\x80\x02\xc4\x02\x97\xc1B\x8d\xd7\x98\xed?\x86\xaa\\\x9f\xbcsK\x17y}\xef\xb9Y4\xd8\xb0\xbaH\x1d\xc3@\x1c\xe0\xa0\x16\xaaPKr\xf6\xd1\x9c\xb5&\xea2uP\xf6\xea\xa0YJ\xd3\'\xd2\xb4\xa1]\x97\xb8\x16+\xa1\x8e\x98a\x83\xc6Pg`U\x0c\xe0\xa0\x80\x18U=\'\x84sB\xe2@F\x10\x16B\xcfj\xbbi\xeb\xf2\xca\\\xfd\xdd\xa7\'d\x9e\x12#\xa6!\x0e\xca\x0ck4rp\x06N\x15\x08\x06\x00\xe8\xfc;\x82\xcb\xd4\x91\xa2!\xc5+\xdc][/\xf6Y\xfa\xd6\xde\xf1\xca\t*\xe4\xa9\xad\xcbF\x11\xac\xaa\x81:\x830\x9f\xe9\xbc\x8f\x8c\x02\xe2\xf0\x9d5\x000@\x14\xd4\xa6jTo\xda\xdc.\x92\xbe\xbdg\xbc6\x86BD\xed]|\xf3\x9fV&\x05\xab\x02U\x18G\xe3C\x93\xa7^\x9aJ\x98Ab\x08\n\xa8\xaa%"@\xa5\x1e\xb8\x16\x92V6\xd0/^/\xd5\xe7\xeb\xb51\x14r\xc6H\xd0Y\xf9\xf2\xc5\xff\xb9\x1c\x8c*\x03\xd6\xa01^ma\xc4\xa4\xea\x03g\x81\r[k\xed\xe2\xe2\xe2\x92B\xb2\xf2\xb2\xa4\xab\xab^+\xa5q\xcc3\xff\xf4\x11\xd3\xd2\x1c\x8c\x06\xc7b\xeb\x98\x1d^\xb4*\x11\xa9%u\xd0$\xe6\xc8\xc0\xd4R\xd3aZ\xba[K\x13\xa5\xe9\xe9i~r\xe7\xceZ5+\xfe8\xea{\xb8\xf0\x93[\xf3\x89\xf5-,\xf9\x98b\x92\x844!\xe4\x8c\x14\x96\xf0\xd2\x82-\x14L\xa1`\x0b\x05\x9b\xd3\x10\x99\xd0\xb1\xe1\x07\xc5G\x7fdz[\x86\x8f\x0c?\xf6\xf8c\x04`\xdd\xbau\xf7\xfc\xfa\x9e\xfb~\xbbEE\x17G\xe9\xeb7\xa6\xbe\x19\xa9F@\x1c\x91%u\x10\x0bu\x04G\xca\xa9\x8fXs\xbd\xf9\xb6\x9f\xaf\xf0k\xec\xee\xbf\xec.\x9f\x9e9\xfe\x9f\xe3\x87\x0f\x1f\xa6f\xbeYk7o\xda\xb4f\xcd\x15wl\xbc\xfd\xa7W\xae\xfd\xef\x07S\xa5\xc3g\xc2D\x9a8\x8e\x1cYR\xe7\x03{\x1f\xafJZni\xcf\xad[6\xfc\xf9\xc7\x7f\xdb\x7f\xe0\xd5\xfd\xaf\xcd\x94g\x9a\xb1\xfb\xbd\xa8\x05\xf0\xc0\xfd\x0f\xac\xbfa\xfd\xbd[\xee\xf5\x0baz\xa8T\x1e:m\xe7C\x04\xd86\xee\xbcuEtc\x9b_\x8a\xbd\x7f\xdd[\xf9\xa6\xb2k\xf7\x93I\x92dY\x06 \x84p.\xba\xe9\xac\xa8\x88\x14\x8b\xc5\x87~\xff\xd0\xec|y\xdb\xf6\x87\x975\xda\xcbo\x9e\xb4\xa0\x8e;V\x9d\xc4\xd4\xce\'vv\xe4\xdb\xf7\xbf\xba\x7fll\x8c\x99E\xe4\xc2\x7fIs\xbao\xeb]\xbbv\r\xbc\xfbV\x96\xa6\xb5Z\xf5\xf9\x97_\xd8\xb6u\xdb\x05\xdb\x9a\xf8?@X\xac\xfc}\x98\xbbI\x00\x00\x00\x00IEND\xaeB`\x82\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x02\x00\x00\x00\xfc\x18\xed\xa3\x00\x00\x06\xcdIDATx\x9c\x9dV[lT\xd7\x15]\xe7\xecs\xee<<\xb6\xb1\xc7\xc6v\x8am\xc0\xd4\xbc\x9a\xd0\x9a&\r\x82 RZ\x92\xb8\xa8\x80\x90\xaa\xaa\x8a\x9a\xb6\x82\x8f\xfe$\x1f|\xf1\x0f(R\xf3\x9d\xa2T\x14\xa9\xe9\x8fQc()\xa5\xe1\xa9&\xe1Y0\x08\x831a0\x18C\xc0c\x9b\xf1x\x9e\x9e{\xcf\xd9\xfd\xb83\xf6\x10\x0c\xa1\xdd\xda:\xda\xba\xf7\x9e\xb5\xceY\xfb1\x03<\x87\r\x0c\x0c\x9c:}&\x9f\xcf\xb25\xc6+\x8c\x8d\x8d|\xfc\xf1_\x8f\x1f?\xfe<{\xbf\xc5\xf6\xef\xdf\xcf\xcc\xc9\xe48[/\x93+\x9c\xefK\x9c\xed\x1bOg\x0b\x93\xf9\xec\xdd\xbb\x83\xcc\xbcs\xe7\xceg#\x88\xa7\xbdhkk\x8b\xc5bCCw_hjb\xc8\xd8\xfd\xec\x89\xcb\x13\xfd\xf7\x98@\x8b\xbf#_\xffA\xa4\xf5\x05\xc7s\'\xfb\xfb\xbf\xea\xe8\xe8\xa8\xa8\xa8\xc8f\xb3\xff\x03\xc1\xd0\xd0P:\x9dn\x9b?\x97\x94~\xf8\xa8\xf0e\xef\xc4\xf9\xaf\n\x93n@\x0b)-\xd83a\xf2:\x16:?Z\x16\xa9\x8fR&\x93>v\xec\xc4\xd2\xa5K\x96,Y\xfa\xed\x04}}}\xbdW\xaf\xaf\xef\\\x17\n\x87\x92i\xef|\xff\xc4\x17Ws\x89\x8c\xa3\xa5\x92\x16\xd2\xb2\xb4\x10\x96\x85\x01<oV\xd8\xacX\x1e^\xf6b$\x14\xe2\xc4\xf8\xf8\xde?\xffe\xd1\xa2\xf6M\x9b6\xcdLp\xe3\xc6\x8d\xf6\xf6\xf6Tj\xa22R\x91+\xf0\xe5X\xfa\xe8\xc5T<IJ:\x04\x08S\x84\xf6i\x84\xf1W\x86\xf1\xe64\x8aWWD\x16,\xac\x10\xd2\x1d~\x18om\x9d\xbbg\xcf\x9e-[\xb6<F\x90\xcf\xe5\x92\x13\xc9h\xb4\x96!c\xf7s\x87\xcf\x8f\xf7\xdc\xb2\xcc\x81JG\x86\x15\x8a\xa0e7\x90\x16\xd2\x14\x9f\xc0c\x05wA\xbb~euuSK\xa0\xe0\xe6o\xdd\xba\xdd\xd2\xdc\\SS\x0b@\xec\xda\xb5k\xfb\xf6\xed\x99L:\x14\n\r\'\xdc\x13\x97\x92\'\xaf\xe4\xb3yGK"\x0bi\xb9B\x8b\x10M\x9f\xfdI\x02i!\x0c\xc3\xb3\xa1\xa0\xf7\xbd\x97\xc3/\xad\xac\xae\x8a\xd2\xa3G\x89\x86\x86\x86\x95+W\x8a\xc1\xc1A\xcfs\xe7\xce\x9dw\xae/\xd9\xf5\xf9\xc4pRk\xa1\xa8\xb4SZ&\x8b\xb0FP\tiY\x9a2\x95,KSFi|\x1aS\x1d\xb5+7E[_\n}\xf8\xc7\x0fkf\xd5(\xc7qB\xc1\x003\xce\xf5g\x86\x13\x81\x80\x94dXZ\xc0ciY1\xa4\x85\xe7\xb2\xd5BK<\xa6\x92\x99>\x84(\xc6,Y\xe6\x1e`\xe8r\xae\xe5\xc5`0\x18PJ)\x00\x0c\x06\xa0Xh\x03\xe5\x7fg\xd1<[V\x87\x10\xbbY\x10FJf\xaf\xc0Z\xc3\x91b:\x19\xe6\t2f\x02\xa4`%\x05\x000\x00\xa8R\x11\xb1\xb4P\x86\x95\x80\xb4Pl\xd7\xaf\xa9\\\xfc\xdd\xd0\xa7\xff\x189s*O\x96\xa4\x85q\x99\x95\xa0\xa9{\x98\xe9\x04\x10C\x82\t\xac\xc0\x02\x96|l\x00\x80\x9c\x8e,+\xaf\xe8\xa2\xc0\xd7z\xd3\xc6\xf0\xfa\x9f\xd5\xadz5@\x9e\xa7<&\x97m\xd6"\xcf\xe4=\xe6\xca\xb2b\xaba\x1dX\r\xab\xc1\xaa\x8c`\xea\x06 \x03e\x98\x04\xc8B\x1a\\:\x97\xd76\xbe~\xd3\xec\xb7~^Ov\xe4\xe2\xc9\x1c\x19\x92\xcc\xd6e\xa1@\x80\xb4\x90\xcc\x84\x923+\x80\xc0\x92-1\x97\x14*#\x90\x96\x95\x07_"\xb2,,]:5I&\xde\xb9y\xf6\x1b\x1b\xeb\xc9\xc4/\x1f\xcb\xfaZq\x81\xa5\x16JN\xa1\xc3\x17\xc7\x8f}\xad\x9e\x94HH\x0b\xf2X\x19(\x8f\xc9\x83\xf2X[\xba\xf2E\xfe\xb3\xaeak\xf1\x93\xcd\xb3\xbf\xbf*(]\xa3\x0ck\xcb\xb2`\x94\xb5\x0eX\x835\xa6\x82\xa2\x93\xf8&\x81\x00XZV\x86\x95\xc7\xca\x94\xb9+\x1e\xdct3I\xcf\tPS\xab\xd6l\x1c\xb0#X\xc3W\xdf:`\x07\xecK\xaf\xc1\x0e\xac\x03V<S\x0e|\x89H0MU\xb7\xc7\xd1F\xf9\xd6;u\xd1\xc6\xc0\xed\xde\xc4\xc5\x03\xa3\x0e\x1c-,\x01J01\x93\x81\x06\x93\x9c\x92\x08\x04\x96\xb0T6\xec\xca\t\xa0<V\x92\xfd\xee\x85\xcbu\x8d\xf2\xcd\xdf\xd45/\x0c\xdf\xe9M\x9c\xf8\xe8kwT\x07\x08\xc4L`U\\A\x96\x95\x82\x96\xf0\xf3\xa1\x84O`g\xaa"\xcb\xaa\xd4h\xc2 \xda(\xdf\xf8]]\xf3\xa2\xf0\x9d\xde\xc4\xc9\x8f\xbe6\xa3:DB\x91\xad\x99\xa3\x9d\xa0\x7fR\x10\x98\x04$\xb80<)\xb2\xacD1\xc93\x97i1\xc9\x12\xd2\x80\x84]\xb5\xb1\xb6yQx\xb07\xf1\xef?\xdd7\xa3:\xa8\x04Y\xaek\xd5\xab\xb7\xcd\tD\xca\x11\x00\x81\x81\x83\xf7\xe2\x7f\x1f\xd3$\xd53%beXYH\x06\t\x1e\xbd\x9d\xbdn&/\xfem\xd8\x8e\xea\x90\x12\x04&\xc1\x9cqG\xaeO\x04*\xfdQ\x00\xe1\x8f{\xe6\xfc\xbd\xb4\x9fm\x05~\xfa\r<&\xd7*-\x15\x98\x18\xd7\x0f\'\tF\xb1\x0e\x92P\x82\t\xac$\xcc\x88\xb9\xba\xfb\xbe\x94\xb6X\xf5\xa2\x98^meHJ?\x96\xccT^E\xe3\xe3\xe3\x05\xb7P\x1b\x8d.\xfcau\xean2\xf3\xc0h)\x94`%$\xc1\xef&\xab\x00\x12\xac\xc0$\xa1@d\xa5\x12\xd3\xcd\xa5\x00\x92\xa5Fc\xab\x9b\x9c\x8a\xa5U\xd6\xda\xf8p\xdcxFtvv\x1e:t\xe8\xce\xe0\x9d\x86\x86\x86|\x02}G\x13\x83\xa7\xd3f\x82\x1d\x02\t(0\t\x9e&\x00\x17\xa1E\t\xba\xf4\x9c,\xab*Y\xb1\xa26\xbc\xba\xaePic\xb1XGGGKKK\xf1\'\x93\x99\xf7\xed\xdb\xf7\xfa\xda5U\x91\xeaG\x03\x85\x9b\x9f\x8d\x8d]\xc9\xca\x82\xd04\x05\x87\x12(\x97\x113\x01\xc4\x96\x1c\x84\x96VF\xd65\xa0Y\x0f\x8f\xc5?\xd9\xf7\xc9\xb6m\xdb\x84\x10S\x9d\x0c!DWWW}tv\xcf\xa5\x9eH\xb3}ek\xd3\xf2-\x8d\xb5\x0bH\xc1\xf3\x9b\xd3\x11\xfe\xea\xbbu\x04\x97\xc6\x83\t\xcd\x0f\xd6\xbe\xd3R\xf5\xdb\x96T]\xe1\x9f\xff:<\xafe\xde\xde\xbd{}t\x94\x8f\xeb\xee\xeen!\xc4\xe9S\xa7\x7f\xf9\x8b_\xdd\x1e\xbaU\xd7\x11X\xfenK\xdb\xe6h\xa8^\xa8\xe2\x84(q\x80\x1dX\xcd&\x10\xa5\xea\x8d\x8d5\xbf\x9fWX\xa2.\xf4\xf6t\xae{\xf3\xdc\xd9s\x00\xae]\xbbVV\xc33\xd9\x91#Gzzz\xde\xfe\xf5\xdb\xd1\xda\xa8\x1b7\xf1\xe3\xf1\xf4\x7f\x92\x94aMP\x80\xb4VEd\xf8\xe5Y\x15k\xea\xbd(\x06\xef\x0e\xbe\xbf\xeb\xfd?|\xf0ASc\xe3\x93PO\xfd\xeb\x18\x89DR\xa9Tww\xf7kk^\xab\nW\xe5nf\xc7\x8f\x0e\x9b\xfe\xb4\x82\x08.\x8eT\xfe\xb4A\xcc\x0f\xc4\x1f\xc5\x0ft\x1fx\xef\xdd\xf7\x1c\xc7q]\xf7iP\xcf\xb2\r\x1b6\x008s\xf6L2\x95\x9cL\xe5\xc7\xbf|\x98\xfc\xfca~"\x17\x1f\x1b9\xf8\xe9A\x00\xcb\x96-\xfb\x7fp\xbfa\xbbw\xef\xde\xbaekl \x96\xcdg\'2\xa9\x0b=\x17\xd6\xfex\xed\x8e\x1d;\x9eg\xef\x7f\x01Lh\x0b\xb1\xc2\x89.o\x00\x00\x00\x00IEND\xaeB`\x82'))
    icon = pystray.Icon("icon", image, "SshTelnet批量工具 v1.6 GUI后台版", menu)    
    # 重新定义点击关闭按钮的处理
    root.bind("<Unmap>", lambda event: hide_window() if root.state() == "iconic" else None)
    threading.Thread(target=icon.run, daemon=True).start()
###########    
    root.mainloop()
