# -*- coding:utf-8 -*-
#!/usr/bin/python3
import warnings 
warnings.filterwarnings("ignore", category=UserWarning, module="cryptography")


import paramiko, telnetlib, threading, xlrd, time, os,shutil
from tkinter import Tk, StringVar, filedialog, messagebox
from tkinter import ttk
from pathlib import Path

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
    if tree.get_children():
        for pre_item in tree.get_children():
            tree.delete(pre_item)

    src_excel = var_hostpath.get()
    dst_dir = var_resultpath.get()
    cmd_dir = var_cmdpath.get()
    wait_time = float(var_time.get())
    socket_max = int(var_socket_max.get())
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
                messagebox.showinfo('提示', '运行结束')
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


if __name__ == '__main__':
    __version__ = "1.6.0.0"
    root = Tk()
    root.resizable(0, 0)
#pyinstall编译时窗口图标可用    
    import base64
    from icon import img
    tmp = open("tmp.ico","wb+")
    tmp.write(base64.b64decode(img))
    tmp.close()
    root.iconbitmap("tmp.ico")
    os.remove("tmp.ico")
#pyinstall编译时窗口图标可用
    root.title('SshTelnet批量工具 v1.6')
    L0 = ttk.Label(root, text='设备清单表格：').grid(row=0, sticky='E')
    L1 = ttk.Label(root, text='结果保存目录：').grid(row=1, sticky='E')
    L2 = ttk.Label(root, text='CMD目录路径：').grid(row=2, sticky='E')
    L3 = ttk.Label(root, text='缓冲延迟时间：').grid(row=3, sticky='E')
    L4 = ttk.Label(root, text='同时执行数量：').grid(row=4, sticky='E')
    var_hostpath = StringVar()
    var_resultpath = StringVar()
    var_cmdpath = StringVar()
    var_time = StringVar()
    var_socket_max = StringVar()
    var_hostpath.set(os.getcwd() + '\\host.xlsx')
    var_resultpath.set(os.getcwd())
    var_cmdpath.set(os.getcwd() + '\\cmd')
    var_time.set(float('0.0'))
    var_socket_max.set(int(20))
    E0 = ttk.Entry(root, textvariable=var_hostpath, width=50).grid(row=0, column=1, sticky='W')
    E1 = ttk.Entry(root, textvariable=var_resultpath, width=50).grid(row=1, column=1, sticky='W')
    E2 = ttk.Entry(root, textvariable=var_cmdpath, width=50).grid(row=2, column=1, sticky='W')
    E3 = ttk.Entry(root, textvariable=var_time, width=10).grid(row=3, column=1, sticky='W')
    E4 = ttk.Entry(root, textvariable=var_socket_max, width=10).grid(row=4, column=1, sticky='W')
    B0 = ttk.Button(root, text='选择文件', command=get_hostfile_path).grid(row=0, column=2, sticky='W')
    B1 = ttk.Button(root, text='保存目录', command=set_result_path).grid(row=1, column=2, sticky='W')
    B2 = ttk.Button(root, text='CMD路径', command=set_cmd_path).grid(row=2, column=2, sticky='W')
    B3 = ttk.Button(root, text='开始运行', command=thread_start).grid(row=3, column=2, rowspan=2, sticky='W')
    tree = ttk.Treeview(root, height=30, show='headings')
    tree['columns'] = ('ID', 'hostname', 'hostip', 'status')
    tree.column('ID', width=50, anchor='center')
    tree.column('hostname', width=300, anchor='center')
    tree.column('hostip', width=200, anchor='center')
    tree.column('status', width=200, anchor='center')
    tree.heading('ID', text='序号', command=(lambda: status_sort(0)))
    tree.heading('hostname', text='设备名称', command=(lambda: status_sort(1)))
    tree.heading('hostip', text='IP地址', command=(lambda: status_sort(2)))
    tree.heading('status', text='运行状态', command=(lambda: status_sort(3)))
    tree.grid(row=5, columnspan=3)
    s1 = ttk.Scrollbar(root)
    s1.grid(row=5, column=3, sticky='NS')
    s1.config(command=(tree.yview))
    tree.config(yscrollcommand=(s1.set))
    root.mainloop()
